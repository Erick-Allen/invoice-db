import { useEffect, useState, type KeyboardEvent } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import { getTagDetail, type TagDetail } from "../api/tags";
import { formatDisplayDate } from "../utils/date";
import { centsToDollars } from "../utils/money";

type TagDetailLocationState = {
    fromInvoiceId?: number;
};

function formatCurrency(cents: number) {
    return cents < 0 ? `-$${centsToDollars(Math.abs(cents))}` : `$${centsToDollars(cents)}`;
}

export function TagDetailPage() {
    const { tagId } = useParams();
    const location = useLocation();
    const navigate = useNavigate();
    const [detail, setDetail] = useState<TagDetail | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const locationState = location.state as TagDetailLocationState | null;
    const backTarget = locationState?.fromInvoiceId ? `/invoices/${locationState.fromInvoiceId}` : "/invoices";
    const backLabel = locationState?.fromInvoiceId ? "Back to invoice" : "Back to invoices";

    useEffect(() => {
        async function loadTagDetail() {
            const parsedTagId = Number(tagId);

            if (!Number.isInteger(parsedTagId) || parsedTagId <= 0) {
                setError("Invalid tag id.");
                setIsLoading(false);
                return;
            }

            try {
                setIsLoading(true);
                setError(null);
                setDetail(await getTagDetail(parsedTagId));
            } catch (err) {
                setError(err instanceof Error ? err.message : "Failed to load tag detail.");
            } finally {
                setIsLoading(false);
            }
        }

        loadTagDetail();
    }, [tagId]);

    function openInvoiceDetail(invoiceId: number) {
        navigate(`/invoices/${invoiceId}`);
    }

    function handleInvoiceRowKeyDown(event: KeyboardEvent<HTMLTableRowElement>, invoiceId: number) {
        if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            openInvoiceDetail(invoiceId);
        }
    }

    return (
        <>
            <div className="page-header">
                <Link className="back-link" to={backTarget}>
                    {backLabel}
                </Link>
                <h2>Tag Detail</h2>
                <p>Review tag usage, money metrics, and invoice history.</p>
            </div>

            {isLoading ? (
                <p>Loading tag...</p>
            ) : error ? (
                <p className="error-message">{error}</p>
            ) : detail ? (
                <section className="detail-stack">
                    <section className="detail-panel">
                        <div>
                            <span className="detail-label">Tag</span>
                            <h3>{detail.tag.name}</h3>
                        </div>
                        <dl className="detail-grid">
                            <div>
                                <dt>Status</dt>
                                <dd><span className="status-badge">{detail.tag.is_active ? "active" : "inactive"}</span></dd>
                            </div>
                            <div>
                                <dt>Description</dt>
                                <dd>{detail.tag.description || "-"}</dd>
                            </div>
                            <div>
                                <dt>Tag ID</dt>
                                <dd>{detail.tag.id}</dd>
                            </div>
                        </dl>
                    </section>

                    <section className="detail-summary-grid" aria-label="Tag money metrics">
                        <div>
                            <span>Invoices</span>
                            <strong>{detail.metrics.invoice_count}</strong>
                        </div>
                        <div>
                            <span>Issued</span>
                            <strong>{detail.metrics.issued_invoice_count}</strong>
                        </div>
                        <div>
                            <span>Total Invoiced</span>
                            <strong>{formatCurrency(detail.metrics.total_invoiced_cents)}</strong>
                        </div>
                        <div>
                            <span>Total Cost</span>
                            <strong>{formatCurrency(detail.metrics.total_cost_cents)}</strong>
                        </div>
                        <div>
                            <span>Total Paid</span>
                            <strong>{formatCurrency(detail.metrics.total_paid_cents)}</strong>
                        </div>
                        <div>
                            <span>Net Profit</span>
                            <strong>{formatCurrency(detail.metrics.net_profit_cents)}</strong>
                        </div>
                        <div>
                            <span>Total Owed</span>
                            <strong>{formatCurrency(detail.metrics.total_owed_cents)}</strong>
                        </div>
                    </section>

                    <section className="detail-panel">
                        <div className="section-header">
                            <h3>Invoices</h3>
                        </div>

                        {detail.invoices.length === 0 ? (
                            <p className="empty-state">No invoices are attached to this tag.</p>
                        ) : (
                            <div className="table-wrapper detail-table-wrapper">
                                <table className="data-table">
                                    <thead>
                                        <tr>
                                            <th>Invoice</th>
                                            <th>Customer</th>
                                            <th>Issued</th>
                                            <th>Due</th>
                                            <th>Status</th>
                                            <th>Total</th>
                                            <th>Cost</th>
                                            <th>Paid</th>
                                            <th>Owed</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {detail.invoices.map((invoice) => (
                                            <tr
                                                key={invoice.id}
                                                className="clickable-row"
                                                tabIndex={0}
                                                aria-label={`View invoice ${invoice.id}`}
                                                onClick={() => openInvoiceDetail(invoice.id)}
                                                onKeyDown={(event) => handleInvoiceRowKeyDown(event, invoice.id)}
                                            >
                                                <td>#{invoice.id}</td>
                                                <td>{invoice.customer_name}</td>
                                                <td>{formatDisplayDate(invoice.date_issued)}</td>
                                                <td>{formatDisplayDate(invoice.date_due)}</td>
                                                <td><span className="status-badge">{invoice.status}</span></td>
                                                <td>{formatCurrency(invoice.total)}</td>
                                                <td>{formatCurrency(invoice.cost_total_cents)}</td>
                                                <td>{formatCurrency(invoice.amount_paid_cents)}</td>
                                                <td>{formatCurrency(invoice.balance_due_cents)}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </section>
                </section>
            ) : (
                <p className="empty-state">Tag not found.</p>
            )}
        </>
    );
}
