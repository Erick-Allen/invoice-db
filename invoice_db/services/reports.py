import sqlite3
from typing import TypedDict

from invoice_db.utils import to_iso

from . import exceptions


class ReportSummary(TypedDict):
    invoice_count: int
    revenue_total_cents: int
    cost_total_cents: int
    profit_total_cents: int
    outstanding_due_cents: int


class StatusBreakdown(TypedDict):
    status: str
    invoice_count: int
    revenue_total_cents: int


class TagPerformance(TypedDict):
    tag_id: int
    tag_name: str
    invoice_count: int
    revenue_total_cents: int
    cost_total_cents: int
    profit_total_cents: int


class ReportingOverview(TypedDict):
    start_date: str | None
    end_date: str | None
    summary: ReportSummary
    status_breakdown: list[StatusBreakdown]
    tag_performance: list[TagPerformance]


def _normalize_report_dates(start_date: str | None, end_date: str | None) -> tuple[str | None, str | None]:
    try:
        normalized_start = to_iso(start_date)
        normalized_end = to_iso(end_date)
    except ValueError as e:
        raise exceptions.ValidationError(str(e)) from e

    if normalized_start is not None and normalized_end is not None and normalized_end < normalized_start:
        raise exceptions.ValidationError("End date cannot be before start date.")

    return normalized_start, normalized_end


def _date_clause(alias: str, start_date: str | None, end_date: str | None) -> tuple[str, list[str]]:
    clauses = []
    params = []

    if start_date is not None:
        clauses.append(f"{alias}.date_issued >= ?")
        params.append(start_date)
    if end_date is not None:
        clauses.append(f"{alias}.date_issued <= ?")
        params.append(end_date)

    return (" AND " + " AND ".join(clauses), params) if clauses else ("", [])


def get_reporting_overview(
    cursor: sqlite3.Cursor,
    *,
    start_date: str | None = None,
    end_date: str | None = None,
) -> ReportingOverview:
    start_date, end_date = _normalize_report_dates(start_date, end_date)
    invoice_date_clause, invoice_date_params = _date_clause("i", start_date, end_date)

    cursor.execute(
        f"""
        WITH invoice_costs AS (
            SELECT
                i.id AS invoice_id,
                i.total AS revenue_total,
                COALESCE(SUM(ii.quantity * ii.unit_cost), 0) AS cost_total,
                COALESCE(p.amount_paid, 0) AS amount_paid
            FROM invoices i
            LEFT JOIN invoice_items ii ON ii.invoice_id = i.id
            LEFT JOIN (
                SELECT invoice_id, SUM(amount_cents) AS amount_paid
                FROM payments
                GROUP BY invoice_id
            ) p ON p.invoice_id = i.id
            WHERE i.status IN ('sent', 'paid'){invoice_date_clause}
            GROUP BY i.id, i.total, p.amount_paid
        )
        SELECT
            COUNT(*) AS invoice_count,
            COALESCE(SUM(revenue_total), 0) AS revenue_total_cents,
            COALESCE(SUM(cost_total), 0) AS cost_total_cents,
            COALESCE(SUM(revenue_total - cost_total), 0) AS profit_total_cents,
            COALESCE(SUM(MAX(revenue_total - amount_paid, 0)), 0) AS outstanding_due_cents
        FROM invoice_costs
        """,
        invoice_date_params,
    )
    summary_row = cursor.fetchone()

    cursor.execute(
        f"""
        SELECT
            i.status,
            COUNT(*) AS invoice_count,
            COALESCE(SUM(i.total), 0) AS revenue_total_cents
        FROM invoices i
        WHERE 1 = 1{invoice_date_clause}
        GROUP BY i.status
        ORDER BY
            CASE i.status
                WHEN 'draft' THEN 1
                WHEN 'sent' THEN 2
                WHEN 'paid' THEN 3
                WHEN 'void' THEN 4
                ELSE 5
            END
        """,
        invoice_date_params,
    )
    status_rows = cursor.fetchall()

    cursor.execute(
        f"""
        WITH invoice_costs AS (
            SELECT
                i.id AS invoice_id,
                i.total AS revenue_total,
                COALESCE(SUM(ii.quantity * ii.unit_cost), 0) AS cost_total
            FROM invoices i
            LEFT JOIN invoice_items ii ON ii.invoice_id = i.id
            WHERE i.status IN ('sent', 'paid'){invoice_date_clause}
            GROUP BY i.id, i.total
        )
        SELECT
            t.id AS tag_id,
            t.name AS tag_name,
            COUNT(DISTINCT ic.invoice_id) AS invoice_count,
            COALESCE(SUM(ic.revenue_total), 0) AS revenue_total_cents,
            COALESCE(SUM(ic.cost_total), 0) AS cost_total_cents,
            COALESCE(SUM(ic.revenue_total - ic.cost_total), 0) AS profit_total_cents
        FROM invoice_costs ic
        JOIN invoice_tags it ON it.invoice_id = ic.invoice_id
        JOIN tags t ON t.id = it.tag_id
        GROUP BY t.id, t.name
        ORDER BY profit_total_cents DESC, revenue_total_cents DESC, t.name
        """,
        invoice_date_params,
    )
    tag_rows = cursor.fetchall()

    return {
        "start_date": start_date,
        "end_date": end_date,
        "summary": {
            "invoice_count": summary_row["invoice_count"] if summary_row else 0,
            "revenue_total_cents": summary_row["revenue_total_cents"] if summary_row else 0,
            "cost_total_cents": summary_row["cost_total_cents"] if summary_row else 0,
            "profit_total_cents": summary_row["profit_total_cents"] if summary_row else 0,
            "outstanding_due_cents": summary_row["outstanding_due_cents"] if summary_row else 0,
        },
        "status_breakdown": [dict(row) for row in status_rows],
        "tag_performance": [dict(row) for row in tag_rows],
    }
