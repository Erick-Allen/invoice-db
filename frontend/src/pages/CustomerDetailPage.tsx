import { useEffect, useMemo, useState, type KeyboardEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { getCustomer, type Customer } from "../api/customers";
import { listInvoices, type Invoice, type InvoiceStatus } from "../api/invoices";
import { getPaymentSummary, type PaymentSummary } from "../api/payments";
import { centsToDollars } from "../utils/money";

type StatusCounts = Record<InvoiceStatus, number>;

const EMPTY_STATUS_COUNTS: StatusCounts = {
    draft: 0,
    sent: 0,
    paid: 0,
    void: 0,
};

function sortInvoicesChronologically(invoices: Invoice[]) {
    return [...invoices].sort((first, second) => {
        const firstDate = first.date_issued ?? "";
        const secondDate = second.date_issued ?? "";

        if (firstDate === secondDate) {
            return first.id - second.id;
        }

        return firstDate.localeCompare(secondDate);
    });
}

export function CustomerDetailPage() {
    const { customerId } = useParams();
    const navigate = useNavigate();
    const [customer, setCustomer] = useState<Customer | null>(null);
    const [invoices, setInvoices] = useState<Invoice[]>([]);
    const [paymentSummaries, setPaymentSummaries] = useState<Record<number, PaymentSummary>>({});
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        async function loadCustomerDetail() {
            const parsedCustomerId = Number(customerId);

            if (!Number.isInteger(parsedCustomerId) || parsedCustomerId <= 0) {
                setError("Invalid customer id.");
                setIsLoading(false);
                return;
            }

            try {
                setIsLoading(true);
                setError(null);

                const [customerData, invoiceData] = await Promise.all([
                    getCustomer(parsedCustomerId),
                    listInvoices({ customerId: parsedCustomerId }),
                ]);
                const paymentSummaryEntries = await Promise.all(
                    invoiceData.map(async (invoice) => [
                        invoice.id,
                        await getPaymentSummary(invoice.id),
                    ] as const)
                );

                setCustomer(customerData);
                setInvoices(sortInvoicesChronologically(invoiceData));
                setPaymentSummaries(Object.fromEntries(paymentSummaryEntries));
            } catch (err) {
                setError(err instanceof Error ? err.message : "Failed to load customer detail.");
            } finally {
                setIsLoading(false);
            }
        }

        loadCustomerDetail();
    }, [customerId]);

    function openInvoiceDetail(invoiceId: number) {
        navigate(`/invoices/${invoiceId}`, { state: { fromCustomerId: customer?.id } });
    }

    function handleInvoiceRowKeyDown(event: KeyboardEvent<HTMLTableRowElement>, invoiceId: number) {
        if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            openInvoiceDetail(invoiceId);
        }
    }

    const summary = useMemo(() => {
        return invoices.reduce(
            (current, invoice) => {
                const paymentSummary = paymentSummaries[invoice.id];

                current.totalInvoicedCents += invoice.total;
                current.totalPaidCents += paymentSummary?.amount_paid_cents ?? 0;
                current.totalOwedCents += paymentSummary?.balance_due_cents ?? invoice.total;
                current.statusCounts[invoice.status] += 1;

                return current;
            },
            {
                totalInvoicedCents: 0,
                totalPaidCents: 0,
                totalOwedCents: 0,
                statusCounts: { ...EMPTY_STATUS_COUNTS },
            }
        );
    }, [invoices, paymentSummaries]);

    return (
        <>
            <div className="page-header">
                <Link className="back-link" to="/customers">
                    Back to customers
                </Link>
                <h2>Customer Detail</h2>
                <p>Review customer profile and invoice history.</p>
            </div>

            {isLoading ? (
                <p>Loading customer...</p>
            ) : error ? (
                <p className="error-message">{error}</p>
            ) : customer ? (
                <section className="detail-stack">
                    <section className="detail-panel">
                        <div>
                            <span className="detail-label">Customer</span>
                            <h3>{customer.name}</h3>
                        </div>
                        <dl className="detail-grid">
                            <div>
                                <dt>Email</dt>
                                <dd>{customer.email}</dd>
                            </div>
                            <div>
                                <dt>Customer ID</dt>
                                <dd>{customer.id}</dd>
                            </div>
                        </dl>
                    </section>

                    <section className="detail-summary-grid" aria-label="Customer invoice summary">
                        <div>
                            <span>Invoices</span>
                            <strong>{invoices.length}</strong>
                        </div>
                        <div>
                            <span>Total Invoiced</span>
                            <strong>${centsToDollars(summary.totalInvoicedCents)}</strong>
                        </div>
                        <div>
                            <span>Total Paid</span>
                            <strong>${centsToDollars(summary.totalPaidCents)}</strong>
                        </div>
                        <div>
                            <span>Total Owed</span>
                            <strong>${centsToDollars(summary.totalOwedCents)}</strong>
                        </div>
                    </section>

                    <section className="status-breakdown" aria-label="Customer invoice status counts">
                        {Object.entries(summary.statusCounts).map(([status, count]) => (
                            <div key={status}>
                                <span>{status}</span>
                                <strong>{count}</strong>
                            </div>
                        ))}
                    </section>

                    <section className="detail-panel">
                        <div className="section-header">
                            <h3>Invoice History</h3>
                        </div>

                        {invoices.length === 0 ? (
                            <p className="empty-state">No invoices found for this customer.</p>
                        ) : (
                            <div className="table-wrapper detail-table-wrapper">
                                <table className="data-table">
                                    <thead>
                                        <tr>
                                            <th>Invoice</th>
                                            <th>Issued</th>
                                            <th>Due</th>
                                            <th>Status</th>
                                            <th>Total</th>
                                            <th>Paid</th>
                                            <th>Owed</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {invoices.map((invoice) => {
                                            const paymentSummary = paymentSummaries[invoice.id];

                                            return (
                                                <tr
                                                    key={invoice.id}
                                                    className="clickable-row"
                                                    tabIndex={0}
                                                    aria-label={`View invoice ${invoice.id}`}
                                                    onClick={() => openInvoiceDetail(invoice.id)}
                                                    onKeyDown={(event) => handleInvoiceRowKeyDown(event, invoice.id)}
                                                >
                                                    <td>#{invoice.id}</td>
                                                    <td>{invoice.date_issued ?? "-"}</td>
                                                    <td>{invoice.date_due ?? "-"}</td>
                                                    <td><span className="status-badge">{invoice.status}</span></td>
                                                    <td>${centsToDollars(invoice.total)}</td>
                                                    <td>${centsToDollars(paymentSummary?.amount_paid_cents ?? 0)}</td>
                                                    <td>${centsToDollars(paymentSummary?.balance_due_cents ?? invoice.total)}</td>
                                                </tr>
                                            );
                                        })}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </section>
                </section>
            ) : (
                <p className="empty-state">Customer not found.</p>
            )}
        </>
    );
}
