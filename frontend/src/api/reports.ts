import { apiRequest } from "./client";

export type ReportSummary = {
    invoice_count: number;
    revenue_total_cents: number;
    cost_total_cents: number;
    profit_total_cents: number;
    outstanding_due_cents: number;
};

export type StatusBreakdown = {
    status: string;
    invoice_count: number;
    revenue_total_cents: number;
};

export type TagPerformance = {
    tag_id: number;
    tag_name: string;
    invoice_count: number;
    revenue_total_cents: number;
    cost_total_cents: number;
    profit_total_cents: number;
};

export type ReportingOverview = {
    start_date: string | null;
    end_date: string | null;
    summary: ReportSummary;
    status_breakdown: StatusBreakdown[];
    tag_performance: TagPerformance[];
};

type ReportingOverviewOptions = {
    startDate?: string;
    endDate?: string;
};

export function getReportingOverview(options: ReportingOverviewOptions = {}) {
    const params = new URLSearchParams();

    if (options.startDate) {
        params.set("start_date", options.startDate);
    }
    if (options.endDate) {
        params.set("end_date", options.endDate);
    }

    const query = params.toString() ? `?${params.toString()}` : "";
    return apiRequest<ReportingOverview>(`/reports/overview/${query}`);
}
