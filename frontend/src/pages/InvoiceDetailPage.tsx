import { useEffect, useMemo, useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import { getCustomer, type Customer } from "../api/customers";
import { createInvoiceItem, deleteInvoiceItem, updateInvoiceItem } from "../api/invoiceItems";
import { getInvoice, type Invoice } from "../api/invoices";
import { listPayments, getPaymentSummary, type Payment, type PaymentSummary } from "../api/payments";
import { listProducts, type Product } from "../api/products";
import { addInvoiceTag, listInvoiceTags, listTags, removeInvoiceTag, type Tag } from "../api/tags";
import { centsToDollars, dollarsToCents } from "../utils/money";

function productLabel(product: Product | undefined, productId: number) {
    return product ? product.name : `Product #${productId}`;
}

function categoryLabel(product: Product | undefined) {
    return product?.category_name ?? "Uncategorized";
}

function restoreScrollPosition(scrollY: number) {
    if (navigator.userAgent.includes("jsdom")) {
        return;
    }

    window.requestAnimationFrame(() => window.scrollTo({ top: scrollY }));
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
    const [tags, setTags] = useState<Tag[]>([]);
    const [invoiceTags, setInvoiceTags] = useState<Tag[]>([]);
    const [newItemProductId, setNewItemProductId] = useState("");
    const [newItemQuantity, setNewItemQuantity] = useState("1");
    const [newItemUnitCostDollars, setNewItemUnitCostDollars] = useState("");
    const [newItemUnitPriceDollars, setNewItemUnitPriceDollars] = useState("");
    const [newTagId, setNewTagId] = useState("");
    const [isItemSubmitting, setIsItemSubmitting] = useState(false);
    const [isTagSubmitting, setIsTagSubmitting] = useState(false);
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
            const [customerData, paymentData, summaryData, productData, tagData, invoiceTagData] = await Promise.all([
                getCustomer(invoiceData.customer_id),
                listPayments(invoiceData.id),
                getPaymentSummary(invoiceData.id),
                listProducts(),
                listTags(true),
                listInvoiceTags(invoiceData.id),
            ]);

            setInvoice(invoiceData);
            setCustomer(customerData);
            setPayments(paymentData);
            setPaymentSummary(summaryData);
            setProducts(productData);
            setTags(tagData);
            setInvoiceTags(invoiceTagData);
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

    const availableTags = useMemo(() => {
        const attachedTagIds = new Set(invoiceTags.map((tag) => tag.id));
        return tags.filter((tag) => !attachedTagIds.has(tag.id));
    }, [tags, invoiceTags]);

    async function handleAddInvoiceItem() {
        if (!invoice) {
            return;
        }

        if (!newItemProductId) {
            setActionError("Product is required.");
            return;
        }

        const productId = Number(newItemProductId);
        const selectedProduct = productsById[productId];
        if (!selectedProduct) {
            setActionError("Product is required.");
            return;
        }

        const quantity = Number(newItemQuantity);
        if (!Number.isInteger(quantity) || quantity <= 0) {
            setActionError("Quantity must be a positive whole number.");
            return;
        }

        let unitCostCents: number | null = null;
        if (newItemUnitCostDollars.trim()) {
            try {
                unitCostCents = dollarsToCents(newItemUnitCostDollars);
            } catch (err) {
                setActionError(err instanceof Error ? err.message : "Enter a valid unit cost.");
                return;
            }
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

        const resolvedUnitCostCents = unitCostCents ?? selectedProduct.cost_cents;
        const resolvedUnitPriceCents = unitPriceCents ?? selectedProduct.unit_price_cents;
        const matchingItem = invoice.items?.find((item) => (
            item.product_id === productId
            && item.unit_cost_cents === resolvedUnitCostCents
            && item.unit_price_cents === resolvedUnitPriceCents
        ));

        try {
            setIsItemSubmitting(true);
            setActionError(null);
            const scrollY = window.scrollY;
            if (matchingItem) {
                await updateInvoiceItem(matchingItem.id, {
                    quantity: matchingItem.quantity + quantity,
                });
            } else {
                await createInvoiceItem(invoice.id, {
                    product_id: productId,
                    quantity,
                    unit_cost_cents: unitCostCents,
                    unit_price_cents: unitPriceCents,
                });
            }
            setNewItemProductId("");
            setNewItemQuantity("1");
            setNewItemUnitCostDollars("");
            setNewItemUnitPriceDollars("");
            await loadInvoiceDetail();
            restoreScrollPosition(scrollY);
        } catch (err) {
            setActionError(err instanceof Error ? err.message : "Failed to add line item.");
        } finally {
            setIsItemSubmitting(false);
        }
    }

    async function handleDeleteInvoiceItem(itemId: number) {
        try {
            setActionError(null);
            const scrollY = window.scrollY;
            await deleteInvoiceItem(itemId);
            await loadInvoiceDetail();
            restoreScrollPosition(scrollY);
        } catch (err) {
            setActionError(err instanceof Error ? err.message : "Failed to delete line item.");
        }
    }

    async function handleChangeInvoiceItemQuantity(itemId: number, quantity: number) {
        if (quantity < 1) {
            return;
        }

        try {
            setActionError(null);
            const scrollY = window.scrollY;
            await updateInvoiceItem(itemId, { quantity });
            await loadInvoiceDetail();
            restoreScrollPosition(scrollY);
        } catch (err) {
            setActionError(err instanceof Error ? err.message : "Failed to update line item quantity.");
        }
    }

    async function handleAddInvoiceTag() {
        if (!invoice) {
            return;
        }

        if (!newTagId) {
            setActionError("Tag is required.");
            return;
        }

        try {
            setIsTagSubmitting(true);
            setActionError(null);
            await addInvoiceTag(invoice.id, { tag_id: Number(newTagId) });
            setNewTagId("");
            await loadInvoiceDetail();
        } catch (err) {
            setActionError(err instanceof Error ? err.message : "Failed to add tag.");
        } finally {
            setIsTagSubmitting(false);
        }
    }

    async function handleRemoveInvoiceTag(tagId: number) {
        if (!invoice) {
            return;
        }

        try {
            setActionError(null);
            await removeInvoiceTag(invoice.id, tagId);
            await loadInvoiceDetail();
        } catch (err) {
            setActionError(err instanceof Error ? err.message : "Failed to remove tag.");
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
                                <dt>Total</dt>
                                <dd>${centsToDollars(invoice.total)}</dd>
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
                            <span>Balance Due</span>
                            <strong>${centsToDollars(paymentSummary?.balance_due_cents ?? invoice.total)}</strong>
                        </div>
                        <div>
                            <span>Paid</span>
                            <strong>${centsToDollars(paymentSummary?.amount_paid_cents ?? 0)}</strong>
                        </div>
                        <div>
                            <span>Cost</span>
                            <strong>${centsToDollars(invoice.cost_total_cents ?? 0)}</strong>
                        </div>
                        <div>
                            <span>Profit</span>
                            <strong>${centsToDollars(invoice.profit_total_cents ?? 0)}</strong>
                        </div>
                    </section>

                    {actionError && <p className="error-message">{actionError}</p>}

                    <section className="detail-panel">
                        <div className="section-header">
                            <h3>Tags</h3>
                        </div>

                        {invoiceTags.length === 0 ? (
                            <p className="empty-state">No tags assigned to this invoice.</p>
                        ) : (
                            <div className="tag-list" aria-label="Invoice tags">
                                {invoiceTags.map((tag) => (
                                    <span className="tag-chip" key={tag.id}>
                                        {tag.name}
                                        <button
                                            type="button"
                                            aria-label={`Remove ${tag.name} tag`}
                                            onClick={() => handleRemoveInvoiceTag(tag.id)}
                                        >
                                            x
                                        </button>
                                    </span>
                                ))}
                            </div>
                        )}

                        <div className="line-item-add detail-add-row">
                            <select
                                aria-label="Tag for invoice"
                                value={newTagId}
                                onChange={(event) => setNewTagId(event.target.value)}
                            >
                                <option value="">Select tag</option>
                                {availableTags.map((tag) => (
                                    <option key={tag.id} value={tag.id}>
                                        {tag.name}
                                    </option>
                                ))}
                            </select>
                            <button
                                className="small-action-button"
                                type="button"
                                onClick={handleAddInvoiceTag}
                                disabled={isTagSubmitting || availableTags.length === 0}
                            >
                                {isTagSubmitting ? "Adding..." : "Add Tag"}
                            </button>
                        </div>
                    </section>

                    <section className="detail-panel">
                        <div className="section-header">
                            <h3>Line Items</h3>
                            <span className="section-count">{invoice.items?.length ?? 0} items</span>
                        </div>

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
                                    aria-label="Unit cost override for new invoice detail item"
                                    type="text"
                                    value={newItemUnitCostDollars}
                                    onChange={(event) => setNewItemUnitCostDollars(event.target.value)}
                                    placeholder="Unit Cost"
                                />
                                <input
                                    aria-label="Unit price override for new invoice detail item"
                                    type="text"
                                    value={newItemUnitPriceDollars}
                                    onChange={(event) => setNewItemUnitPriceDollars(event.target.value)}
                                    placeholder="Unit Price"
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
                                            <th>Unit Cost</th>
                                            <th>Total Cost</th>
                                            <th>Unit Price</th>
                                            <th>Total Price</th>
                                            <th>Profit</th>
                                            {invoice.status === "draft" && <th>Actions</th>}
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {invoice.items.map((item) => (
                                            <tr key={item.id}>
                                                <td>{productLabel(productsById[item.product_id], item.product_id)}</td>
                                                <td>{categoryLabel(productsById[item.product_id])}</td>
                                                <td>
                                                    {invoice.status === "draft" ? (
                                                        <div className="quantity-stepper">
                                                            <button
                                                                type="button"
                                                                aria-label={`Decrease quantity for ${productLabel(productsById[item.product_id], item.product_id)}`}
                                                                onClick={() => handleChangeInvoiceItemQuantity(item.id, item.quantity - 1)}
                                                                disabled={item.quantity <= 1}
                                                            >
                                                                -
                                                            </button>
                                                            <span>{item.quantity}</span>
                                                            <button
                                                                type="button"
                                                                aria-label={`Increase quantity for ${productLabel(productsById[item.product_id], item.product_id)}`}
                                                                onClick={() => handleChangeInvoiceItemQuantity(item.id, item.quantity + 1)}
                                                            >
                                                                +
                                                            </button>
                                                        </div>
                                                    ) : (
                                                        item.quantity
                                                    )}
                                                </td>
                                                <td>${centsToDollars(item.unit_cost_cents)}</td>
                                                <td>${centsToDollars(item.cost_total_cents)}</td>
                                                <td>${centsToDollars(item.unit_price_cents)}</td>
                                                <td>${centsToDollars(item.line_total_cents)}</td>
                                                <td>${centsToDollars(item.profit_total_cents)}</td>
                                                {invoice.status === "draft" && (
                                                    <td>
                                                        <button
                                                            className="small-action-button"
                                                            type="button"
                                                            onClick={() => handleDeleteInvoiceItem(item.id)}
                                                        >
                                                            Delete
                                                        </button>
                                                    </td>
                                                )}
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
