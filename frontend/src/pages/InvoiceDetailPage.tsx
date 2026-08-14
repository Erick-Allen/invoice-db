import { useEffect, useMemo, useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import { getCustomer, type Customer } from "../api/customers";
import { createInvoiceItem } from "../api/invoiceItems";
import { getInvoice, type Invoice } from "../api/invoices";
import { listPayments, getPaymentSummary, type Payment, type PaymentSummary } from "../api/payments";
import { listProducts, type Product } from "../api/products";
import { centsToDollars, dollarsToCents } from "../utils/money";

function productLabel(product: Product | undefined, productId: number) {
    return product ? product.name : `Product #${productId}`;
}

function categoryLabel(product: Product | undefined) {
    return product?.category_name ?? "Uncategorized";
}

type InvoiceDetailLocationState = {
    fromCustomerId?: number;
};

export function InvoiceDetailPage() {
    const { invoiceId } = useParams();
    const location = useLocation();
    const [invoice, setInvoice] = useState<Invoice | null>(null);
    const [customer, setCustomer] = useState<Customer | null>(null);
    const [payments, setPayments] = useState<Payment[]>([]);
    const [paymentSummary, setPaymentSummary] = useState<PaymentSummary | null>(null);
    const [products, setProducts] = useState<Product[]>([]);
    const [newItemProductId, setNewItemProductId] = useState("");
    const [newItemQuantity, setNewItemQuantity] = useState("1");
    const [newItemUnitPriceDollars, setNewItemUnitPriceDollars] = useState("");
    const [isItemSubmitting, setIsItemSubmitting] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [actionError, setActionError] = useState<string | null>(null);
    const locationState = location.state as InvoiceDetailLocationState | null;
    const backTarget = locationState?.fromCustomerId ? `/customers/${locationState.fromCustomerId}` : "/invoices";
    const backLabel = locationState?.fromCustomerId ? "Back to customer" : "Back to invoices";

    function handlePrintInvoice() {
        window.print();
    }

    async function loadInvoiceDetail() {
        const parsedInvoiceId = Number(invoiceId);

        if (!Number.isInteger(parsedInvoiceId) || parsedInvoiceId <= 0) {
            setError("Invalid invoice id.");
            setIsLoading(false);
            return;
        }

        try {
            setIsLoading(true);
            setError(null);

            const invoiceData = await getInvoice(parsedInvoiceId, true);
            const [customerData, paymentData, summaryData, productData] = await Promise.all([
                getCustomer(invoiceData.customer_id),
                listPayments(invoiceData.id),
                getPaymentSummary(invoiceData.id),
                listProducts(),
            ]);

            setInvoice(invoiceData);
            setCustomer(customerData);
            setPayments(paymentData);
            setPaymentSummary(summaryData);
            setProducts(productData);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to load invoice detail.");
        } finally {
            setIsLoading(false);
        }
    }

    useEffect(() => {
        loadInvoiceDetail();
    }, [invoiceId]);

    const productsById = useMemo(() => {
        return Object.fromEntries(products.map((product) => [product.id, product]));
    }, [products]);

    const activeProducts = useMemo(() => {
        return products.filter((product) => product.is_active);
    }, [products]);

    async function handleAddInvoiceItem() {
        if (!invoice) {
            return;
        }

        if (!newItemProductId) {
            setActionError("Product is required.");
            return;
        }

        const quantity = Number(newItemQuantity);
        if (!Number.isInteger(quantity) || quantity <= 0) {
            setActionError("Quantity must be a positive whole number.");
            return;
        }

        let unitPriceCents: number | null = null;
        if (newItemUnitPriceDollars.trim()) {
            try {
                unitPriceCents = dollarsToCents(newItemUnitPriceDollars);
            } catch (err) {
                setActionError(err instanceof Error ? err.message : "Enter a valid unit price.");
                return;
            }
        }

        try {
            setIsItemSubmitting(true);
            setActionError(null);
            await createInvoiceItem(invoice.id, {
                product_id: Number(newItemProductId),
                quantity,
                unit_price_cents: unitPriceCents,
            });
            setNewItemProductId("");
            setNewItemQuantity("1");
            setNewItemUnitPriceDollars("");
            await loadInvoiceDetail();
        } catch (err) {
            setActionError(err instanceof Error ? err.message : "Failed to add line item.");
        } finally {
            setIsItemSubmitting(false);
        }
    }

    return (
        <>
            <div className="page-header">
                <div className="detail-header-actions print-hidden">
                    <Link className="back-link" to={backTarget}>
                        {backLabel}
                    </Link>
                    <button className="action-button" type="button" onClick={handlePrintInvoice}>
                        Print
                    </button>
                </div>
                <h2>{invoice ? `Invoice #${invoice.id}` : "Invoice Detail"}</h2>
                <p>Review invoice customer, line items, and payment history.</p>
            </div>

            {isLoading ? (
                <p>Loading invoice...</p>
            ) : error ? (
                <p className="error-message">{error}</p>
            ) : invoice ? (
                <>
                    <section className="invoice-print-document print-only" aria-label="Printable customer invoice">
                        <header className="invoice-print-header">
                            <div>
                                <p className="invoice-print-brand">InvoiceDB</p>
                                <h1>Invoice #{invoice.id}</h1>
                            </div>
                            <dl>
                                <div>
                                    <dt>Issued</dt>
                                    <dd>{invoice.date_issued ?? "-"}</dd>
                                </div>
                                <div>
                                    <dt>Due</dt>
                                    <dd>{invoice.date_due ?? "-"}</dd>
                                </div>
                            </dl>
                        </header>

                        <section className="invoice-print-bill-to">
                            <span>Bill To</span>
                            <strong>{customer ? customer.name : `Customer #${invoice.customer_id}`}</strong>
                            {customer?.email && <p>{customer.email}</p>}
                        </section>

                        <section className="invoice-print-section">
                            <h2>Line Items</h2>
                            {!invoice.items || invoice.items.length === 0 ? (
                                <p>No line items found for this invoice.</p>
                            ) : (
                                <table className="invoice-print-table">
                                    <thead>
                                        <tr>
                                            <th>Product</th>
                                            <th>Category</th>
                                            <th>Quantity</th>
                                            <th>Unit Price</th>
                                            <th>Amount</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {invoice.items.map((item) => (
                                            <tr key={item.id}>
                                                <td>{productLabel(productsById[item.product_id], item.product_id)}</td>
                                                <td>{categoryLabel(productsById[item.product_id])}</td>
                                                <td>{item.quantity}</td>
                                                <td>${centsToDollars(item.unit_price_cents)}</td>
                                                <td>${centsToDollars(item.line_total_cents)}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            )}
                        </section>

                        <section className="invoice-print-totals" aria-label="Printable invoice totals">
                            <dl>
                                <div>
                                    <dt>Total</dt>
                                    <dd>${centsToDollars(invoice.total)}</dd>
                                </div>
                                <div>
                                    <dt>Amount Paid</dt>
                                    <dd>${centsToDollars(paymentSummary?.amount_paid_cents ?? 0)}</dd>
                                </div>
                                <div className="invoice-print-balance">
                                    <dt>Balance Due</dt>
                                    <dd>${centsToDollars(paymentSummary?.balance_due_cents ?? invoice.total)}</dd>
                                </div>
                            </dl>
                        </section>
                    </section>

                    <section className="detail-stack screen-only">
                    <section className="detail-panel">
                        <div>
                            <span className="detail-label">Invoice</span>
                            <h3>#{invoice.id}</h3>
                        </div>
                        <dl className="detail-grid">
                            <div>
                                <dt>Customer</dt>
                                <dd>{customer ? customer.name : `Customer #${invoice.customer_id}`}</dd>
                            </div>
                            <div>
                                <dt>Status</dt>
                                <dd><span className="status-badge">{invoice.status}</span></dd>
                            </div>
                            <div>
                                <dt>Issued</dt>
                                <dd>{invoice.date_issued ?? "-"}</dd>
                            </div>
                            <div>
                                <dt>Due</dt>
                                <dd>{invoice.date_due ?? "-"}</dd>
                            </div>
                        </dl>
                    </section>

                    <section className="detail-summary-grid" aria-label="Invoice payment summary">
                        <div>
                            <span>Total</span>
                            <strong>${centsToDollars(invoice.total)}</strong>
                        </div>
                        <div>
                            <span>Paid</span>
                            <strong>${centsToDollars(paymentSummary?.amount_paid_cents ?? 0)}</strong>
                        </div>
                        <div>
                            <span>Balance Due</span>
                            <strong>${centsToDollars(paymentSummary?.balance_due_cents ?? invoice.total)}</strong>
                        </div>
                        <div>
                            <span>Line Items</span>
                            <strong>{invoice.items?.length ?? 0}</strong>
                        </div>
                    </section>

                    <section className="detail-panel">
                        <div className="section-header">
                            <h3>Line Items</h3>
                        </div>

                        {actionError && <p className="error-message">{actionError}</p>}

                        {invoice.status === "draft" && (
                            <div className="line-item-add detail-add-row">
                                <select
                                    aria-label="Product for new invoice detail item"
                                    value={newItemProductId}
                                    onChange={(event) => setNewItemProductId(event.target.value)}
                                >
                                    <option value="">Select product</option>
                                    {activeProducts.map((product) => (
                                        <option key={product.id} value={product.id}>
                                            {product.name} - ${centsToDollars(product.unit_price_cents)}
                                        </option>
                                    ))}
                                </select>
                                <input
                                    aria-label="Quantity for new invoice detail item"
                                    type="number"
                                    min="1"
                                    value={newItemQuantity}
                                    onChange={(event) => setNewItemQuantity(event.target.value)}
                                />
                                <input
                                    aria-label="Unit price override for new invoice detail item"
                                    type="text"
                                    value={newItemUnitPriceDollars}
                                    onChange={(event) => setNewItemUnitPriceDollars(event.target.value)}
                                    placeholder="Override"
                                />
                                <button
                                    className="small-action-button"
                                    type="button"
                                    onClick={handleAddInvoiceItem}
                                    disabled={isItemSubmitting}
                                >
                                    {isItemSubmitting ? "Adding..." : "Add Item"}
                                </button>
                            </div>
                        )}

                        {!invoice.items || invoice.items.length === 0 ? (
                            <p className="empty-state">No line items found for this invoice.</p>
                        ) : (
                            <div className="table-wrapper detail-table-wrapper">
                                <table className="data-table">
                                    <thead>
                                        <tr>
                                            <th>Product</th>
                                            <th>Category</th>
                                            <th>Quantity</th>
                                            <th>Unit Price</th>
                                            <th>Line Total</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {invoice.items.map((item) => (
                                            <tr key={item.id}>
                                                <td>{productLabel(productsById[item.product_id], item.product_id)}</td>
                                                <td>{categoryLabel(productsById[item.product_id])}</td>
                                                <td>{item.quantity}</td>
                                                <td>${centsToDollars(item.unit_price_cents)}</td>
                                                <td>${centsToDollars(item.line_total_cents)}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </section>

                    <section className="detail-panel">
                        <div className="section-header">
                            <h3>Payments</h3>
                        </div>

                        {payments.length === 0 ? (
                            <p className="empty-state">No payments found for this invoice.</p>
                        ) : (
                            <div className="table-wrapper detail-table-wrapper">
                                <table className="data-table">
                                    <thead>
                                        <tr>
                                            <th>Date</th>
                                            <th>Method</th>
                                            <th>Amount</th>
                                            <th>Note</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {payments.map((payment) => (
                                            <tr key={payment.id}>
                                                <td>{payment.payment_date}</td>
                                                <td>{payment.method}</td>
                                                <td>${centsToDollars(payment.amount_cents)}</td>
                                                <td>{payment.note || "-"}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </section>
                    </section>
                </>
            ) : (
                <p className="empty-state">Invoice not found.</p>
            )}
        </>
    );
}
