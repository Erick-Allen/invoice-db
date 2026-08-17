import { useEffect, useState, type KeyboardEvent, type MouseEvent, type SubmitEventHandler } from "react";
import { useNavigate } from "react-router-dom";
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
import { createInvoiceItem } from "../api/invoiceItems";
import { listProducts, type Product } from "../api/products";
import {
    createTag,
    deactivateTag,
    deleteTag,
    listTags,
    updateTag,
    type Tag,
} from "../api/tags";
import { AssistantChatBox } from "../components/AssistantChatBox";

type CreateInvoiceItemForm = {
    productId: string;
    quantity: string;
    unitPriceDollars: string;
};

export function InvoicesPage() {
    const navigate = useNavigate();
    const [customers, setCustomers] = useState<Customer[]>([]);
    const [products, setProducts] = useState<Product[]>([]);
    const [invoices, setInvoices] = useState<Invoice[]>([]);
    const [tags, setTags] = useState<Tag[]>([]);
    const [activeTab, setActiveTab] = useState<"invoices" | "tags">("invoices");

    const [customerId, setCustomerId] = useState("");
    const [dateIssued, setDateIssued] = useState("");
    const [dateDue, setDateDue] = useState("");
    const [createLineItems, setCreateLineItems] = useState<CreateInvoiceItemForm[]>([
        { productId: "", quantity: "1", unitPriceDollars: "" },
    ]);
    const [isCreateOverlayOpen, setIsCreateOverlayOpen] = useState(false);

    const [editingInvoiceId, setEditingInvoiceId] = useState<number | null>(null);
    const [editCustomerId, setEditCustomerId] = useState("");
    const [editDateIssued, setEditDateIssued] = useState("");
    const [editDateDue, setEditDateDue] = useState("");

    const [tagName, setTagName] = useState("");
    const [tagDescription, setTagDescription] = useState("");
    const [isCreateTagOverlayOpen, setIsCreateTagOverlayOpen] = useState(false);
    const [editingTagId, setEditingTagId] = useState<number | null>(null);
    const [editTagName, setEditTagName] = useState("");
    const [editTagDescription, setEditTagDescription] = useState("");
    const [editTagIsActive, setEditTagIsActive] = useState(true);

    const [isLoading, setIsLoading] = useState(true);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [loadError, setLoadError] = useState<string | null>(null);

    async function loadData() {
        try {
            setIsLoading(true);
            setError(null);
            setLoadError(null);

            const [customerData, productData, invoiceData, tagData] = await Promise.all([
                listCustomers(),
                listProducts(true),
                listInvoices(true),
                listTags(),
            ]);

            setCustomers(customerData);
            setProducts(productData);
            setInvoices(invoiceData);
            setTags(tagData);
        } catch (err) {
            const message = err instanceof Error ? err.message : "Unknown error.";
            setLoadError(`Failed to load invoices and line items. ${message}`);
        } finally {
            setIsLoading(false);
        }
    }

    useEffect(() => {
        loadData();
    }, []);

    function resetCreateForm() {
        setCustomerId("");
        setDateIssued("");
        setDateDue("");
        setCreateLineItems([{ productId: "", quantity: "1", unitPriceDollars: "" }]);
    }

    function openCreateOverlay() {
        setError(null);
        setIsCreateOverlayOpen(true);
    }

    function closeCreateOverlay() {
        if (isSubmitting) {
            return;
        }

        resetCreateForm();
        setIsCreateOverlayOpen(false);
    }

    const handleSubmit: SubmitEventHandler<HTMLFormElement> = async (event) => {
        event.preventDefault();

        if (!customerId) {
            setError("Customer is required.");
            return;
        }

        const selectedLineItems = createLineItems.filter((item) => item.productId);
        if (selectedLineItems.length === 0) {
            setError("At least one line item is required.");
            return;
        }

        const preparedLineItems = [];
        for (const item of selectedLineItems) {
            const quantity = Number(item.quantity);
            if (!Number.isInteger(quantity) || quantity <= 0) {
                setError("Line item quantity must be a positive whole number.");
                return;
            }

            let unitPriceCents: number | null = null;
            if (item.unitPriceDollars.trim()) {
                try {
                    unitPriceCents = dollarsToCents(item.unitPriceDollars);
                } catch (err) {
                    setError(err instanceof Error ? err.message : "Enter a valid unit price.");
                    return;
                }
            }

            preparedLineItems.push({
                product_id: Number(item.productId),
                quantity,
                unit_price_cents: unitPriceCents,
            });
        }

        try {
            setIsSubmitting(true);
            setError(null);

            const invoice = await createInvoice({
                customer_id: Number(customerId),
                date_issued: dateIssued || null,
                date_due: dateDue || null,
            });

            for (const item of preparedLineItems) {
                await createInvoiceItem(invoice.id, item);
            }

            resetCreateForm();
            setIsCreateOverlayOpen(false);

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

    function resetCreateTagForm() {
        setTagName("");
        setTagDescription("");
    }

    function openCreateTagOverlay() {
        setError(null);
        setIsCreateTagOverlayOpen(true);
    }

    function closeCreateTagOverlay() {
        if (isSubmitting) {
            return;
        }

        resetCreateTagForm();
        setIsCreateTagOverlayOpen(false);
    }

    function startEditingTag(tag: Tag) {
        setEditingTagId(tag.id);
        setEditTagName(tag.name);
        setEditTagDescription(tag.description ?? "");
        setEditTagIsActive(tag.is_active);
    }

    function cancelEditingTag() {
        setEditingTagId(null);
        setEditTagName("");
        setEditTagDescription("");
        setEditTagIsActive(true);
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

    const handleCreateTag: SubmitEventHandler<HTMLFormElement> = async (event) => {
        event.preventDefault();

        const trimmedName = tagName.trim();
        if (!trimmedName) {
            setError("Tag name is required.");
            return;
        }

        try {
            setIsSubmitting(true);
            setError(null);
            await createTag({
                name: trimmedName,
                description: tagDescription.trim() || null,
                is_active: true,
            });
            resetCreateTagForm();
            setIsCreateTagOverlayOpen(false);
            await loadData();
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to create tag.");
        } finally {
            setIsSubmitting(false);
        }
    };

    async function handleUpdateTag(tagId: number) {
        const trimmedName = editTagName.trim();
        if (!trimmedName) {
            setError("Tag name is required.");
            return;
        }

        try {
            setError(null);
            await updateTag(tagId, {
                name: trimmedName,
                description: editTagDescription.trim() || null,
                is_active: editTagIsActive,
            });
            cancelEditingTag();
            await loadData();
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to update tag.");
        }
    }

    async function handleDeactivateTag(tagId: number) {
        try {
            setError(null);
            await deactivateTag(tagId);
            await loadData();
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to deactivate tag.");
        }
    }

    async function handleDeleteTag(tagId: number) {
        const confirmed = window.confirm("Are you sure you want to delete this tag?");
        if (!confirmed) {
            return;
        }

        try {
            setError(null);
            await deleteTag(tagId);
            await loadData();
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to delete tag.");
        }
    }

    function getCustomerName(id: number) {
        const customer = customers.find((customer) => customer.id === id);
        return customer ? customer.name : `Customer #${id}`;
    }

    function addCreateLineItem() {
        setCreateLineItems((current) => [
            ...current,
            { productId: "", quantity: "1", unitPriceDollars: "" },
        ]);
    }

    function updateCreateLineItem(index: number, changes: Partial<CreateInvoiceItemForm>) {
        setCreateLineItems((current) =>
            current.map((item, itemIndex) =>
                itemIndex === index ? { ...item, ...changes } : item
            )
        );
    }

    function removeCreateLineItem(index: number) {
        setCreateLineItems((current) =>
            current.length === 1
                ? [{ productId: "", quantity: "1", unitPriceDollars: "" }]
                : current.filter((_, itemIndex) => itemIndex !== index)
        );
    }

    function isInteractiveTarget(target: EventTarget | null) {
        return target instanceof HTMLElement && Boolean(target.closest("button, input, select, textarea, a"));
    }

    function openInvoiceDetail(invoiceId: number) {
        navigate(`/invoices/${invoiceId}`);
    }

    function handleInvoiceRowClick(event: MouseEvent<HTMLTableRowElement>, invoiceId: number) {
        if (isInteractiveTarget(event.target)) {
            return;
        }

        openInvoiceDetail(invoiceId);
    }

    function handleInvoiceRowKeyDown(event: KeyboardEvent<HTMLTableRowElement>, invoiceId: number) {
        if (isInteractiveTarget(event.target)) {
            return;
        }

        if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            openInvoiceDetail(invoiceId);
        }
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

    return (
        <>
            <div className="page-header">
                <h2>Invoices</h2>
                <p>Create draft invoices and manage line items.</p>
            </div>

            <section className="invoice-page-stack">
                {error && <p className="error-message">{error}</p>}

                <AssistantChatBox />
                <div className="section-header">
                    <div className="segmented-tabs" role="tablist" aria-label="Invoice sections">
                        <button
                            type="button"
                            className={activeTab === "invoices" ? "active" : ""}
                            onClick={() => setActiveTab("invoices")}
                        >
                            Invoices
                        </button>
                        <button
                            type="button"
                            className={activeTab === "tags" ? "active" : ""}
                            onClick={() => setActiveTab("tags")}
                        >
                            Tags
                        </button>
                    </div>
                    <div className="section-actions">
                        {activeTab === "invoices" ? (
                            <button className="primary-button" type="button" onClick={openCreateOverlay}>
                                Create Invoice
                            </button>
                        ) : (
                            <button className="primary-button" type="button" onClick={openCreateTagOverlay}>
                                Create Tag
                            </button>
                        )}
                    </div>
                </div>

                {isCreateOverlayOpen && (
                    <div className="modal-overlay" role="presentation" onMouseDown={closeCreateOverlay}>
                        <form
                            onSubmit={handleSubmit}
                            className="form-card modal-panel"
                            role="dialog"
                            aria-modal="true"
                            aria-labelledby="create-invoice-title"
                            onMouseDown={(event) => event.stopPropagation()}
                        >
                            <div className="modal-header">
                                <h3 id="create-invoice-title">Create Invoice</h3>
                                <button className="icon-button" type="button" aria-label="Close create invoice" onClick={closeCreateOverlay}>
                                    x
                                </button>
                            </div>

                            <div className="form-grid modal-form-grid">
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

                                <div className="form-field">
                                    <label>Line Items</label>
                                    <div className="line-item-list">
                                        {createLineItems.map((item, index) => (
                                            <div className="line-item-add" key={index}>
                                                <select
                                                    aria-label={`Product for new invoice item ${index + 1}`}
                                                    value={item.productId}
                                                    onChange={(event) => updateCreateLineItem(index, { productId: event.target.value })}
                                                >
                                                    <option value="">Select product</option>
                                                    {products.map((product) => (
                                                        <option key={product.id} value={product.id}>
                                                            {product.name} - ${centsToDollars(product.unit_price_cents)}
                                                        </option>
                                                    ))}
                                                </select>
                                                <input
                                                    aria-label={`Quantity for new invoice item ${index + 1}`}
                                                    type="number"
                                                    min="1"
                                                    value={item.quantity}
                                                    onChange={(event) => updateCreateLineItem(index, { quantity: event.target.value })}
                                                />
                                                <input
                                                    aria-label={`Unit price override for new invoice item ${index + 1}`}
                                                    type="text"
                                                    value={item.unitPriceDollars}
                                                    onChange={(event) => updateCreateLineItem(index, { unitPriceDollars: event.target.value })}
                                                    placeholder="Override"
                                                />
                                                <button
                                                    className="small-danger-button"
                                                    type="button"
                                                    onClick={() => removeCreateLineItem(index)}
                                                >
                                                    Remove
                                                </button>
                                            </div>
                                        ))}
                                    </div>
                                    <button className="small-action-button" type="button" onClick={addCreateLineItem}>
                                        Add Item
                                    </button>
                                </div>

                                <div className="modal-actions">
                                    <button className="secondary-button" type="button" onClick={closeCreateOverlay} disabled={isSubmitting}>
                                        Cancel
                                    </button>
                                    <button className="primary-button" type="submit" disabled={isSubmitting}>
                                        {isSubmitting ? "Creating..." : "Create Invoice"}
                                    </button>
                                </div>
                            </div>
                        </form>
                    </div>
                )}

                {activeTab === "invoices" && (
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
                                    <th>Change Status</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>

                            <tbody>
                                {invoices.map((invoice, index) => {
                                    const items = getInvoiceItems(invoice);

                                    return (
                                        <tr
                                            key={invoice.id}
                                            className={editingInvoiceId === invoice.id ? undefined : "clickable-row"}
                                            tabIndex={editingInvoiceId === invoice.id ? undefined : 0}
                                            aria-label={editingInvoiceId === invoice.id ? undefined : `View invoice ${invoice.id}`}
                                            onClick={editingInvoiceId === invoice.id ? undefined : (event) => handleInvoiceRowClick(event, invoice.id)}
                                            onKeyDown={editingInvoiceId === invoice.id ? undefined : (event) => handleInvoiceRowKeyDown(event, invoice.id)}
                                        >
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
                                                        {items.length} item{items.length === 1 ? "" : "s"}
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
                )}

                {activeTab === "tags" && (
                    <section className="invoice-page-stack">
                        {isCreateTagOverlayOpen && (
                            <div className="modal-overlay" role="presentation" onMouseDown={closeCreateTagOverlay}>
                                <form
                                    className="form-card modal-panel"
                                    onSubmit={handleCreateTag}
                                    role="dialog"
                                    aria-modal="true"
                                    aria-labelledby="create-tag-title"
                                    onMouseDown={(event) => event.stopPropagation()}
                                >
                                    <div className="modal-header">
                                        <h3 id="create-tag-title">Create Tag</h3>
                                        <button className="icon-button" type="button" aria-label="Close create tag" onClick={closeCreateTagOverlay}>
                                            x
                                        </button>
                                    </div>

                                    <div className="form-grid modal-form-grid">
                                        <div className="form-field">
                                            <label htmlFor="tag-name">Name</label>
                                            <input
                                                id="tag-name"
                                                type="text"
                                                value={tagName}
                                                onChange={(event) => setTagName(event.target.value)}
                                                placeholder="Commercial"
                                            />
                                        </div>
                                        <div className="form-field">
                                            <label htmlFor="tag-description">Description</label>
                                            <input
                                                id="tag-description"
                                                type="text"
                                                value={tagDescription}
                                                onChange={(event) => setTagDescription(event.target.value)}
                                                placeholder="Invoice reporting context"
                                            />
                                        </div>
                                        <div className="modal-actions">
                                            <button className="secondary-button" type="button" onClick={closeCreateTagOverlay} disabled={isSubmitting}>
                                                Cancel
                                            </button>
                                            <button className="primary-button" type="submit" disabled={isSubmitting}>
                                                {isSubmitting ? "Creating..." : "Create Tag"}
                                            </button>
                                        </div>
                                    </div>
                                </form>
                            </div>
                        )}

                        <div className="table-wrapper wide-table-wrapper">
                            {isLoading ? (
                                <p>Loading tags...</p>
                            ) : tags.length === 0 ? (
                                <p className="empty-state">No tags found.</p>
                            ) : (
                                <table className="data-table">
                                    <thead>
                                        <tr>
                                            <th>Name</th>
                                            <th>Description</th>
                                            <th>Status</th>
                                            <th>Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {tags.map((tag) => (
                                            <tr key={tag.id}>
                                                {editingTagId === tag.id ? (
                                                    <>
                                                        <td>
                                                            <input
                                                                type="text"
                                                                value={editTagName}
                                                                onChange={(event) => setEditTagName(event.target.value)}
                                                            />
                                                        </td>
                                                        <td>
                                                            <input
                                                                className="wide-select"
                                                                type="text"
                                                                value={editTagDescription}
                                                                onChange={(event) => setEditTagDescription(event.target.value)}
                                                            />
                                                        </td>
                                                        <td>
                                                            <select
                                                                value={editTagIsActive ? "active" : "inactive"}
                                                                onChange={(event) => setEditTagIsActive(event.target.value === "active")}
                                                            >
                                                                <option value="active">Active</option>
                                                                <option value="inactive">Inactive</option>
                                                            </select>
                                                        </td>
                                                        <td>
                                                            <div className="name-actions">
                                                                <button className="small-action-button" type="button" onClick={() => handleUpdateTag(tag.id)}>
                                                                    Save
                                                                </button>
                                                                <button className="small-danger-button" type="button" onClick={cancelEditingTag}>
                                                                    Cancel
                                                                </button>
                                                            </div>
                                                        </td>
                                                    </>
                                                ) : (
                                                    <>
                                                        <td><strong>{tag.name}</strong></td>
                                                        <td className="muted-table-cell">{tag.description ?? "-"}</td>
                                                        <td>
                                                            <span className="status-badge">
                                                                {tag.is_active ? "active" : "inactive"}
                                                            </span>
                                                        </td>
                                                        <td>
                                                            <div className="name-actions">
                                                                <button className="small-action-button" type="button" onClick={() => startEditingTag(tag)}>
                                                                    Edit
                                                                </button>
                                                                {tag.is_active && (
                                                                    <button className="small-action-button" type="button" onClick={() => handleDeactivateTag(tag.id)}>
                                                                        Deactivate
                                                                    </button>
                                                                )}
                                                                <button className="small-danger-button" type="button" onClick={() => handleDeleteTag(tag.id)}>
                                                                    Delete
                                                                </button>
                                                            </div>
                                                        </td>
                                                    </>
                                                )}
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            )}
                        </div>
                    </section>
                )}
            </section>
        </>
    );
}
