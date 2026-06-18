import { useEffect, useState, type SubmitEventHandler } from "react";
import { centsToDollars, dollarsToCents } from "../utils/money";
import { listCustomers, type Customer } from "../api/customers";
import {
    createInvoice,
    deleteInvoice,
    listInvoices,
    updateInvoice,
    updateInvoiceStatus,
    type Invoice,
    type InvoiceStatus,
} from "../api/invoices";
import {
    createInvoiceItem,
    deleteInvoiceItem,
    updateInvoiceItem,
    type InvoiceItem,
} from "../api/invoiceItems";
import {
    createPayment,
    deletePayment,
    getPaymentSummary,
    listPayments,
    PAYMENT_METHODS,
    type Payment,
    type PaymentMethod,
    type PaymentSummary,
} from "../api/payments";
import { listProducts, type Product } from "../api/products";
import { AssistantChatBox } from "../components/AssistantChatBox";

type LineItemForm = {
    productId: string;
    quantity: string;
    unitPriceDollars: string;
};

type PaymentForm = {
    amountDollars: string;
    paymentDate: string;
    method: PaymentMethod;
    note: string;
};

export function InvoicesPage() {
    const [customers, setCustomers] = useState<Customer[]>([]);
    const [products, setProducts] = useState<Product[]>([]);
    const [invoices, setInvoices] = useState<Invoice[]>([]);
    const [paymentSummaries, setPaymentSummaries] = useState<Record<number, PaymentSummary>>({});
    const [paymentsByInvoice, setPaymentsByInvoice] = useState<Record<number, Payment[]>>({});

    const [customerId, setCustomerId] = useState("");
    const [dateIssued, setDateIssued] = useState("");
    const [dateDue, setDateDue] = useState("");

    const [editingInvoiceId, setEditingInvoiceId] = useState<number | null>(null);
    const [editCustomerId, setEditCustomerId] = useState("");
    const [editDateIssued, setEditDateIssued] = useState("");
    const [editDateDue, setEditDateDue] = useState("");

    const [lineItemForms, setLineItemForms] = useState<Record<number, LineItemForm>>({});
    const [paymentForms, setPaymentForms] = useState<Record<number, PaymentForm>>({});
    const [editingItemId, setEditingItemId] = useState<number | null>(null);
    const [editItemProductId, setEditItemProductId] = useState("");
    const [editItemQuantity, setEditItemQuantity] = useState("");
    const [editItemUnitPriceDollars, setEditItemUnitPriceDollars] = useState("");

    const [isLoading, setIsLoading] = useState(true);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [loadError, setLoadError] = useState<string | null>(null);

    async function loadData() {
        try {
            setIsLoading(true);
            setError(null);
            setLoadError(null);

            const [customerData, productData, invoiceData] = await Promise.all([
                listCustomers(),
                listProducts(true),
                listInvoices(true),
            ]);
            const paymentSummaryEntries = await Promise.all(
                invoiceData.map(async (invoice) => [
                    invoice.id,
                    await getPaymentSummary(invoice.id),
                ] as const)
            );
            const paymentEntries = await Promise.all(
                invoiceData.map(async (invoice) => [
                    invoice.id,
                    await listPayments(invoice.id),
                ] as const)
            );

            setCustomers(customerData);
            setProducts(productData);
            setInvoices(invoiceData);
            setPaymentSummaries(Object.fromEntries(paymentSummaryEntries));
            setPaymentsByInvoice(Object.fromEntries(paymentEntries));
        } catch (err) {
            const message = err instanceof Error ? err.message : "Unknown error.";
            setLoadError(`Failed to load invoices, line items, and payments. ${message}`);
        } finally {
            setIsLoading(false);
        }
    }

    useEffect(() => {
        loadData();
    }, []);

    const handleSubmit: SubmitEventHandler<HTMLFormElement> = async (event) => {
        event.preventDefault();

        if (!customerId) {
            setError("Customer is required.");
            return;
        }

        try {
            setIsSubmitting(true);
            setError(null);

            await createInvoice({
                customer_id: Number(customerId),
                date_issued: dateIssued || null,
                date_due: dateDue || null,
            });

            setCustomerId("");
            setDateIssued("");
            setDateDue("");

            await loadData();
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to create invoice.");
        } finally {
            setIsSubmitting(false);
        }
    };

    function startEditingInvoice(invoice: Invoice) {
        setEditingInvoiceId(invoice.id);
        setEditCustomerId(String(invoice.customer_id));
        setEditDateIssued(invoice.date_issued ?? "");
        setEditDateDue(invoice.date_due ?? "");
    }

    function cancelEditingInvoice() {
        setEditingInvoiceId(null);
        setEditCustomerId("");
        setEditDateIssued("");
        setEditDateDue("");
    }

    async function handleUpdateInvoice(invoiceId: number) {
        if (!editCustomerId) {
            setError("Customer is required.");
            return;
        }

        const existingInvoice = invoices.find((invoice) => invoice.id === invoiceId);

        if (!existingInvoice) {
            setError("Invoice not found.");
            return;
        }

        const noChangesDetected =
            existingInvoice.customer_id === Number(editCustomerId) &&
            (existingInvoice.date_issued ?? "") === editDateIssued &&
            (existingInvoice.date_due ?? "") === editDateDue;

        if (noChangesDetected) {
            setError(null);
            cancelEditingInvoice();
            return;
        }

        try {
            setError(null);

            await updateInvoice(invoiceId, {
                customer_id: Number(editCustomerId),
                date_issued: editDateIssued || null,
                date_due: editDateDue || null,
            });

            cancelEditingInvoice();
            await loadData();
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to update invoice.");
        }
    }

    async function handleStatusChange(invoiceId: number, nextStatus: InvoiceStatus) {
        try {
            setError(null);
            await updateInvoiceStatus(invoiceId, nextStatus);
            await loadData();
        } catch (err) {
            const message = err instanceof Error ? err.message : "Failed to update status.";
            setError(`Could not change invoice status. ${message}`);
        }
    }

    async function handleDeleteInvoice(invoiceId: number) {
        const confirmed = window.confirm("Are you sure you want to delete this invoice?");

        if (!confirmed) {
            return;
        }

        try {
            setError(null);
            await deleteInvoice(invoiceId);
            await loadData();
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to delete invoice.");
        }
    }

    function updateLineItemForm(invoiceId: number, changes: Partial<LineItemForm>) {
        setLineItemForms((current) => ({
            ...current,
            [invoiceId]: {
                ...(current[invoiceId] ?? { productId: "", quantity: "1", unitPriceDollars: "" }),
                ...changes,
            },
        }));
    }

    function updatePaymentForm(invoiceId: number, changes: Partial<PaymentForm>) {
        setPaymentForms((current) => ({
            ...current,
            [invoiceId]: {
                ...(current[invoiceId] ?? {
                    amountDollars: "",
                    paymentDate: new Date().toISOString().slice(0, 10),
                    method: "cash",
                    note: "",
                }),
                ...changes,
            },
        }));
    }

    async function handleAddInvoiceItem(invoiceId: number) {
        const form = lineItemForms[invoiceId] ?? { productId: "", quantity: "1", unitPriceDollars: "" };

        if (!form.productId) {
            setError("Product is required.");
            return;
        }

        const quantity = Number(form.quantity);
        if (!Number.isInteger(quantity) || quantity <= 0) {
            setError("Quantity must be a positive whole number.");
            return;
        }

        let unitPriceCents: number | null = null;
        if (form.unitPriceDollars.trim()) {
            try {
                unitPriceCents = dollarsToCents(form.unitPriceDollars);
            } catch (err) {
                setError(err instanceof Error ? err.message : "Enter a valid unit price.");
                return;
            }
        }

        try {
            setError(null);
            await createInvoiceItem(invoiceId, {
                product_id: Number(form.productId),
                quantity,
                unit_price_cents: unitPriceCents,
            });
            updateLineItemForm(invoiceId, { productId: "", quantity: "1", unitPriceDollars: "" });
            await loadData();
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to add line item.");
        }
    }

    function startEditingItem(item: InvoiceItem) {
        setEditingItemId(item.id);
        setEditItemProductId(String(item.product_id));
        setEditItemQuantity(String(item.quantity));
        setEditItemUnitPriceDollars(centsToDollars(item.unit_price_cents));
    }

    function cancelEditingItem() {
        setEditingItemId(null);
        setEditItemProductId("");
        setEditItemQuantity("");
        setEditItemUnitPriceDollars("");
    }

    async function handleUpdateInvoiceItem(itemId: number) {
        if (!editItemProductId) {
            setError("Product is required.");
            return;
        }

        const quantity = Number(editItemQuantity);
        if (!Number.isInteger(quantity) || quantity <= 0) {
            setError("Quantity must be a positive whole number.");
            return;
        }

        let unitPriceCents: number;
        try {
            unitPriceCents = dollarsToCents(editItemUnitPriceDollars);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Enter a valid unit price.");
            return;
        }

        try {
            setError(null);
            await updateInvoiceItem(itemId, {
                product_id: Number(editItemProductId),
                quantity,
                unit_price_cents: unitPriceCents,
            });
            cancelEditingItem();
            await loadData();
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to update line item.");
        }
    }

    async function handleDeleteInvoiceItem(itemId: number) {
        const confirmed = window.confirm("Are you sure you want to delete this line item?");

        if (!confirmed) {
            return;
        }

        try {
            setError(null);
            await deleteInvoiceItem(itemId);
            await loadData();
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to delete line item.");
        }
    }

    async function handleAddPayment(invoiceId: number) {
        const form = paymentForms[invoiceId] ?? {
            amountDollars: "",
            paymentDate: new Date().toISOString().slice(0, 10),
            method: "cash",
            note: "",
        };

        let amountCents: number;
        try {
            amountCents = dollarsToCents(form.amountDollars);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Enter a valid payment amount.");
            return;
        }

        if (!form.paymentDate) {
            setError("Payment date is required.");
            return;
        }

        try {
            setError(null);
            await createPayment(invoiceId, {
                amount_cents: amountCents,
                payment_date: form.paymentDate,
                method: form.method,
                note: form.note.trim() || null,
            });
            updatePaymentForm(invoiceId, { amountDollars: "", note: "" });
            await loadData();
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to add payment.");
        }
    }

    async function handlePayBalance(invoiceId: number, balanceDueCents: number) {
        const form = paymentForms[invoiceId] ?? {
            amountDollars: "",
            paymentDate: new Date().toISOString().slice(0, 10),
            method: "cash",
            note: "",
        };

        if (balanceDueCents <= 0) {
            setError("Invoice has no balance due.");
            return;
        }

        if (!form.paymentDate) {
            setError("Payment date is required.");
            return;
        }

        try {
            setError(null);
            await createPayment(invoiceId, {
                amount_cents: balanceDueCents,
                payment_date: form.paymentDate,
                method: form.method,
                note: form.note.trim() || null,
            });
            updatePaymentForm(invoiceId, { amountDollars: "", note: "" });
            await loadData();
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to pay balance.");
        }
    }

    async function handleDeletePayment(paymentId: number) {
        const confirmed = window.confirm("Are you sure you want to delete this payment?");

        if (!confirmed) {
            return;
        }

        try {
            setError(null);
            await deletePayment(paymentId);
            await loadData();
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to delete payment.");
        }
    }

    function getCustomerName(id: number) {
        const customer = customers.find((customer) => customer.id === id);
        return customer ? customer.name : `Customer #${id}`;
    }

    function getProductName(id: number) {
        const product = products.find((product) => product.id === id);
        return product ? product.name : `Product #${id}`;
    }

    function getNextStatuses(status: InvoiceStatus): InvoiceStatus[] {
        switch (status) {
            case "draft":
                return ["sent"];
            case "sent":
                return ["void"];
            case "paid":
            case "void":
                return [];
            default:
                return [];
        }
    }

    function getInvoiceItems(invoice: Invoice) {
        return invoice.items ?? [];
    }

    function getPaymentSummaryForInvoice(invoice: Invoice) {
        return paymentSummaries[invoice.id] ?? {
            invoice_id: invoice.id,
            invoice_total_cents: invoice.total,
            amount_paid_cents: 0,
            balance_due_cents: invoice.total,
            is_paid: invoice.status === "paid",
        };
    }

    function getPaymentsForInvoice(invoice: Invoice) {
        return paymentsByInvoice[invoice.id] ?? [];
    }

    return (
        <>
            <div className="page-header">
                <h2>Invoices</h2>
                <p>Create draft invoices and manage line items.</p>
            </div>

            <section className="invoice-page-stack">
                {error && <p className="error-message">{error}</p>}

                <form onSubmit={handleSubmit} className="form-card">
                    <div>
                        <h3>Create Invoice</h3>
                    </div>

                    <div className="form-grid">
                        <div className="form-field">
                            <label htmlFor="customer">Customer</label>
                            <select
                                id="customer"
                                value={customerId}
                                onChange={(event) => setCustomerId(event.target.value)}
                            >
                                <option value="">Select a customer</option>
                                {customers.map((customer) => (
                                    <option key={customer.id} value={customer.id}>
                                        {customer.name} - {customer.email}
                                    </option>
                                ))}
                            </select>
                        </div>

                        <div className="form-field">
                            <label htmlFor="dateIssued">Date Issued</label>
                            <input
                                id="dateIssued"
                                type="date"
                                value={dateIssued}
                                onChange={(event) => setDateIssued(event.target.value)}
                            />
                        </div>

                        <div className="form-field">
                            <label htmlFor="dateDue">Date Due</label>
                            <input
                                id="dateDue"
                                type="date"
                                value={dateDue}
                                onChange={(event) => setDateDue(event.target.value)}
                            />
                        </div>

                        <button className="primary-button" type="submit" disabled={isSubmitting}>
                            {isSubmitting ? "Creating..." : "Create Invoice"}
                        </button>
                    </div>
                </form>

                <AssistantChatBox />
                <h3>Invoice List</h3>

                <div className="table-wrapper">
                    {isLoading ? (
                        <p>Loading Invoices...</p>
                    ) : loadError ? (
                        <div className="empty-state">
                            <p>{loadError}</p>
                            <button className="action-button" type="button" onClick={loadData}>
                                Retry
                            </button>
                        </div>
                    ) : invoices.length === 0 ? (
                        <p className="empty-state">No invoices found.</p>
                    ) : (
                        <table className="data-table">
                            <thead>
                                <tr>
                                    <th>#</th>
                                    <th>Customer</th>
                                    <th>Date Issued</th>
                                    <th>Date Due</th>
                                    <th>Total</th>
                                    <th>Status</th>
                                    <th>Line Items</th>
                                    <th>Payments</th>
                                    <th>Change Status</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>

                            <tbody>
                                {invoices.map((invoice, index) => {
                                    const items = getInvoiceItems(invoice);
                                    const form = lineItemForms[invoice.id] ?? {
                                        productId: "",
                                        quantity: "1",
                                        unitPriceDollars: "",
                                    };
                                    const isDraft = invoice.status === "draft";
                                    const paymentSummary = getPaymentSummaryForInvoice(invoice);
                                    const payments = getPaymentsForInvoice(invoice);
                                    const paymentForm = paymentForms[invoice.id] ?? {
                                        amountDollars: "",
                                        paymentDate: new Date().toISOString().slice(0, 10),
                                        method: "cash",
                                        note: "",
                                    };
                                    const canAddPayment = invoice.status === "sent" && paymentSummary.balance_due_cents > 0;

                                    return (
                                        <tr key={invoice.id}>
                                            <td>{index + 1}</td>

                                            {editingInvoiceId === invoice.id ? (
                                                <>
                                                    <td>
                                                        <select
                                                            className="wide-select"
                                                            value={editCustomerId}
                                                            onChange={(event) => setEditCustomerId(event.target.value)}
                                                        >
                                                            <option value="">Select a customer</option>
                                                            {customers.map((customer) => (
                                                                <option key={customer.id} value={customer.id}>
                                                                    {customer.name} - {customer.email}
                                                                </option>
                                                            ))}
                                                        </select>
                                                    </td>
                                                    <td>
                                                        <input
                                                            type="date"
                                                            value={editDateIssued}
                                                            onChange={(event) => setEditDateIssued(event.target.value)}
                                                        />
                                                    </td>
                                                    <td>
                                                        <input
                                                            type="date"
                                                            value={editDateDue}
                                                            onChange={(event) => setEditDateDue(event.target.value)}
                                                        />
                                                    </td>
                                                    <td>${centsToDollars(invoice.total)}</td>
                                                    <td>
                                                        <span className="status-badge">{invoice.status}</span>
                                                    </td>
                                                    <td>{items.length} item{items.length === 1 ? "" : "s"}</td>
                                                    <td>
                                                        Paid ${centsToDollars(paymentSummary.amount_paid_cents)}
                                                    </td>
                                                    <td>
                                                        <span>Editing</span>
                                                    </td>
                                                    <td>
                                                        <div className="name-actions">
                                                            <button
                                                                className="small-action-button"
                                                                type="button"
                                                                onClick={() => handleUpdateInvoice(invoice.id)}
                                                            >
                                                                Save
                                                            </button>

                                                            <button
                                                                className="small-danger-button"
                                                                type="button"
                                                                onClick={cancelEditingInvoice}
                                                            >
                                                                Cancel
                                                            </button>
                                                        </div>
                                                    </td>
                                                </>
                                            ) : (
                                                <>
                                                    <td>{getCustomerName(invoice.customer_id)}</td>
                                                    <td>{invoice.date_issued ?? "-"}</td>
                                                    <td>{invoice.date_due ?? "-"}</td>
                                                    <td>${centsToDollars(invoice.total)}</td>
                                                    <td>
                                                        <span className="status-badge">{invoice.status}</span>
                                                    </td>
                                                    <td>
                                                        <div className="line-items-cell">
                                                            {items.length === 0 ? (
                                                                <p className="muted-text">No line items</p>
                                                            ) : (
                                                                <ul className="line-item-list">
                                                                    {items.map((item) => (
                                                                        <li key={item.id}>
                                                                            {editingItemId === item.id ? (
                                                                                <div className="line-item-edit">
                                                                                    <select
                                                                                        value={editItemProductId}
                                                                                        onChange={(event) => setEditItemProductId(event.target.value)}
                                                                                    >
                                                                                        <option value="">Select product</option>
                                                                                        {products.map((product) => (
                                                                                            <option key={product.id} value={product.id}>
                                                                                                {product.name}
                                                                                            </option>
                                                                                        ))}
                                                                                    </select>
                                                                                    <input
                                                                                        aria-label="Edit quantity"
                                                                                        type="number"
                                                                                        min="1"
                                                                                        value={editItemQuantity}
                                                                                        onChange={(event) => setEditItemQuantity(event.target.value)}
                                                                                    />
                                                                                    <input
                                                                                        aria-label="Edit unit price"
                                                                                        type="text"
                                                                                        value={editItemUnitPriceDollars}
                                                                                        onChange={(event) => setEditItemUnitPriceDollars(event.target.value)}
                                                                                    />
                                                                                    <button
                                                                                        className="small-action-button"
                                                                                        type="button"
                                                                                        onClick={() => handleUpdateInvoiceItem(item.id)}
                                                                                    >
                                                                                        Save
                                                                                    </button>
                                                                                    <button
                                                                                        className="small-danger-button"
                                                                                        type="button"
                                                                                        onClick={cancelEditingItem}
                                                                                    >
                                                                                        Cancel
                                                                                    </button>
                                                                                </div>
                                                                            ) : (
                                                                                <div className="line-item-row">
                                                                                    <span>
                                                                                        {getProductName(item.product_id)} x {item.quantity}
                                                                                    </span>
                                                                                    <span>${centsToDollars(item.line_total_cents)}</span>
                                                                                    {isDraft && (
                                                                                        <div className="name-actions">
                                                                                            <button
                                                                                                className="small-action-button"
                                                                                                type="button"
                                                                                                onClick={() => startEditingItem(item)}
                                                                                            >
                                                                                                Edit
                                                                                            </button>
                                                                                            <button
                                                                                                className="small-danger-button"
                                                                                                type="button"
                                                                                                onClick={() => handleDeleteInvoiceItem(item.id)}
                                                                                            >
                                                                                                Delete
                                                                                            </button>
                                                                                        </div>
                                                                                    )}
                                                                                </div>
                                                                            )}
                                                                        </li>
                                                                    ))}
                                                                </ul>
                                                            )}

                                                            {isDraft && (
                                                                <div className="line-item-add">
                                                                    <select
                                                                        aria-label={`Product for invoice ${invoice.id}`}
                                                                        value={form.productId}
                                                                        onChange={(event) => updateLineItemForm(invoice.id, { productId: event.target.value })}
                                                                    >
                                                                        <option value="">Add product</option>
                                                                        {products.map((product) => (
                                                                            <option key={product.id} value={product.id}>
                                                                                {product.name} - ${centsToDollars(product.unit_price_cents)}
                                                                            </option>
                                                                        ))}
                                                                    </select>
                                                                    <input
                                                                        aria-label={`Quantity for invoice ${invoice.id}`}
                                                                        type="number"
                                                                        min="1"
                                                                        value={form.quantity}
                                                                        onChange={(event) => updateLineItemForm(invoice.id, { quantity: event.target.value })}
                                                                    />
                                                                    <input
                                                                        aria-label={`Unit price override for invoice ${invoice.id}`}
                                                                        type="text"
                                                                        value={form.unitPriceDollars}
                                                                        onChange={(event) => updateLineItemForm(invoice.id, { unitPriceDollars: event.target.value })}
                                                                        placeholder="Override"
                                                                    />
                                                                    <button
                                                                        className="small-action-button"
                                                                        type="button"
                                                                        onClick={() => handleAddInvoiceItem(invoice.id)}
                                                                    >
                                                                        Add
                                                                    </button>
                                                                </div>
                                                            )}
                                                        </div>
                                                    </td>
                                                    <td>
                                                        <div className="payments-cell">
                                                            <div className="payment-summary-grid">
                                                                <span>Total ${centsToDollars(paymentSummary.invoice_total_cents)}</span>
                                                                <span>Paid ${centsToDollars(paymentSummary.amount_paid_cents)}</span>
                                                                <span>Due ${centsToDollars(paymentSummary.balance_due_cents)}</span>
                                                            </div>

                                                            {payments.length === 0 ? (
                                                                <p className="muted-text">No payments</p>
                                                            ) : (
                                                                <ul className="payment-list">
                                                                    {payments.map((payment) => (
                                                                        <li key={payment.id} className="payment-row">
                                                                            <span>
                                                                                ${centsToDollars(payment.amount_cents)} {payment.method} on {payment.payment_date}
                                                                            </span>
                                                                            {invoice.status !== "void" && (
                                                                                <button
                                                                                    className="small-danger-button"
                                                                                    type="button"
                                                                                    onClick={() => handleDeletePayment(payment.id)}
                                                                                >
                                                                                    Delete
                                                                                </button>
                                                                            )}
                                                                        </li>
                                                                    ))}
                                                                </ul>
                                                            )}

                                                            {canAddPayment && (
                                                                <div className="payment-add">
                                                                    <input
                                                                        aria-label={`Payment amount for invoice ${invoice.id}`}
                                                                        type="text"
                                                                        value={paymentForm.amountDollars}
                                                                        onChange={(event) => updatePaymentForm(invoice.id, { amountDollars: event.target.value })}
                                                                        placeholder="Amount"
                                                                    />
                                                                    <input
                                                                        aria-label={`Payment date for invoice ${invoice.id}`}
                                                                        type="date"
                                                                        value={paymentForm.paymentDate}
                                                                        onChange={(event) => updatePaymentForm(invoice.id, { paymentDate: event.target.value })}
                                                                    />
                                                                    <select
                                                                        aria-label={`Payment method for invoice ${invoice.id}`}
                                                                        value={paymentForm.method}
                                                                        onChange={(event) => updatePaymentForm(invoice.id, { method: event.target.value as PaymentMethod })}
                                                                    >
                                                                        {PAYMENT_METHODS.map((method) => (
                                                                            <option key={method} value={method}>
                                                                                {method}
                                                                            </option>
                                                                        ))}
                                                                    </select>
                                                                    <input
                                                                        aria-label={`Payment note for invoice ${invoice.id}`}
                                                                        type="text"
                                                                        value={paymentForm.note}
                                                                        onChange={(event) => updatePaymentForm(invoice.id, { note: event.target.value })}
                                                                        placeholder="Note"
                                                                    />
                                                                    <button
                                                                        className="small-action-button"
                                                                        type="button"
                                                                        onClick={() => handleAddPayment(invoice.id)}
                                                                    >
                                                                        Add
                                                                    </button>
                                                                    <button
                                                                        className="small-action-button"
                                                                        type="button"
                                                                        onClick={() => handlePayBalance(invoice.id, paymentSummary.balance_due_cents)}
                                                                    >
                                                                        Pay Balance
                                                                    </button>
                                                                </div>
                                                            )}
                                                        </div>
                                                    </td>
                                                    <td>
                                                        {getNextStatuses(invoice.status).length === 0 ? (
                                                            <span>No actions</span>
                                                        ) : (
                                                            getNextStatuses(invoice.status).map((nextStatus) => (
                                                                <button
                                                                    className="action-button"
                                                                    key={nextStatus}
                                                                    type="button"
                                                                    onClick={() => handleStatusChange(invoice.id, nextStatus)}
                                                                >
                                                                    {nextStatus}
                                                                </button>
                                                            ))
                                                        )}
                                                    </td>
                                                    <td>
                                                        <div className="name-actions">
                                                            <button
                                                                className="small-action-button"
                                                                type="button"
                                                                onClick={() => startEditingInvoice(invoice)}
                                                            >
                                                                Edit
                                                            </button>
                                                            <button
                                                                className="small-danger-button"
                                                                type="button"
                                                                onClick={() => handleDeleteInvoice(invoice.id)}
                                                            >
                                                                Delete
                                                            </button>
                                                        </div>
                                                    </td>
                                                </>
                                            )}
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    )}
                </div>
            </section>
        </>
    );
}
