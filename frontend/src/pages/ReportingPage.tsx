import { useEffect, useState, type FormEvent } from "react";
import { getReportingOverview, type ReportingOverview } from "../api/reports";
import { centsToDollars } from "../utils/money";

function formatCurrency(cents: number) {
    return `$${centsToDollars(cents)}`;
}

export function ReportingPage() {
    const [report, setReport] = useState<ReportingOverview | null>(null);
    const [startDate, setStartDate] = useState("");
    const [endDate, setEndDate] = useState("");
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState("");

    async function loadReport(options: { startDate?: string; endDate?: string } = {}) {
        try {
            setIsLoading(true);
            setError("");
            const data = await getReportingOverview(options);
            setReport(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to load report data.");
        } finally {
            setIsLoading(false);
        }
    }

    useEffect(() => {
        loadReport();
    }, []);

    function handleSubmit(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        loadReport({
            startDate: startDate || undefined,
            endDate: endDate || undefined,
        });
    }

    function handleClearFilters() {
        setStartDate("");
        setEndDate("");
        loadReport();
    }

    return (
        <>
            <div className="page-header">
                <h2>Reporting</h2>
                <p>Analyze revenue, cost, profit, invoice status, and tag performance.</p>
            </div>

            <section className="reporting-stack">
                <form className="reporting-filters" onSubmit={handleSubmit}>
                    <label>
                        Start Date
                        <input
                            type="date"
                            value={startDate}
                            onChange={(event) => setStartDate(event.target.value)}
                        />
                    </label>
                    <label>
                        End Date
                        <input
                            type="date"
                            value={endDate}
                            onChange={(event) => setEndDate(event.target.value)}
                        />
                    </label>
                    <button className="small-action-button" type="submit">
                        Apply
                    </button>
                    <button className="small-action-button" type="button" onClick={handleClearFilters}>
                        Clear
                    </button>
                </form>

                {error && <p className="error-message">{error}</p>}

                {isLoading ? (
                    <p>Loading report...</p>
                ) : report ? (
                    <>
                        <section className="reporting-summary-grid" aria-label="Reporting performance summary">
                            <div className="reporting-summary-revenue">
                                <span>Revenue</span>
                                <strong>{formatCurrency(report.summary.revenue_total_cents)}</strong>
                            </div>
                            <div className="reporting-summary-outstanding">
                                <span>Outstanding Due</span>
                                <strong>{formatCurrency(report.summary.outstanding_due_cents)}</strong>
                            </div>
                            <div className="reporting-summary-cost">
                                <span>Cost</span>
                                <strong>{formatCurrency(report.summary.cost_total_cents)}</strong>
                            </div>
                            <div className="reporting-summary-profit">
                                <span>Profit</span>
                                <strong>{formatCurrency(report.summary.profit_total_cents)}</strong>
                            </div>
                        </section>

                        <section className="detail-panel">
                            <div className="section-header">
                                <h3>Invoice Status</h3>
                                <span className="section-count">{report.summary.invoice_count} invoices</span>
                            </div>

                            {report.status_breakdown.length === 0 ? (
                                <p className="empty-state">No invoice status data found.</p>
                            ) : (
                                <div className="table-wrapper detail-table-wrapper">
                                    <table className="data-table">
                                        <thead>
                                            <tr>
                                                <th>Status</th>
                                                <th>Invoices</th>
                                                <th>Revenue</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {report.status_breakdown.map((status) => (
                                                <tr key={status.status}>
                                                    <td><span className="status-badge">{status.status}</span></td>
                                                    <td>{status.invoice_count}</td>
                                                    <td>{formatCurrency(status.revenue_total_cents)}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            )}
                        </section>

                        <section className="detail-panel">
                            <div className="section-header">
                                <h3>Tag Performance</h3>
                                <span className="section-count">{report.tag_performance.length} tags</span>
                            </div>

                            {report.tag_performance.length === 0 ? (
                                <p className="empty-state">No tagged invoice performance found.</p>
                            ) : (
                                <div className="table-wrapper detail-table-wrapper">
                                    <table className="data-table">
                                        <thead>
                                            <tr>
                                                <th>Tag</th>
                                                <th>Invoices</th>
                                                <th>Revenue</th>
                                                <th>Cost</th>
                                                <th>Profit</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {report.tag_performance.map((tag) => (
                                                <tr key={tag.tag_id}>
                                                    <td>{tag.tag_name}</td>
                                                    <td>{tag.invoice_count}</td>
                                                    <td>{formatCurrency(tag.revenue_total_cents)}</td>
                                                    <td>{formatCurrency(tag.cost_total_cents)}</td>
                                                    <td>{formatCurrency(tag.profit_total_cents)}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            )}
                        </section>
                    </>
                ) : null}
            </section>
        </>
    );
}
