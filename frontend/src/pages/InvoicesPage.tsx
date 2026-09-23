import { useEffect, useState, type KeyboardEvent, type MouseEvent, type SubmitEventHandler } from "react";
import { useNavigate } from "react-router-dom";
import { centsToDollars, dollarsToCents } from "../utils/money";
import { formatDisplayDate } from "../utils/date";
import { listCustomerLocations, listCustomers, type Customer, type CustomerLocation } from "../api/customers";
import {
    createInvoice,
    deleteInvoice,
    listInvoices,
    type Invoice,
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
    unitCostDollars: string;
    unitPriceDollars: string;
};

export function InvoicesPage() {
    const navigate = useNavigate();
    const [customers, setCustomers] = useState<Customer[]>([]);
    const [customerLocations, setCustomerLocations] = useState<Record<number, CustomerLocation[]>>({});
    const [products, setProducts] = useState<Product[]>([]);
    const [invoices, setInvoices] = useState<Invoice[]>([]);
    const [tags, setTags] = useState<Tag[]>([]);
    const [activeTab, setActiveTab] = useState<"invoices" | "tags">("invoices");

    const [invoiceTitle, setInvoiceTitle] = useState("");
    const [invoiceDescription, setInvoiceDescription] = useState("");
    const [customerId, setCustomerId] = useState("");
    const [locationId, setLocationId] = useState("");
    const [createLineItems, setCreateLineItems] = useState<CreateInvoiceItemForm[]>([
        { productId: "", quantity: "1", unitCostDollars: "", unitPriceDollars: "" },
    ]);
    const [isCreateOverlayOpen, setIsCreateOverlayOpen] = useState(false);

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
            const locationEntries = await Promise.all(
                customerData.map(async (customer) => [
                    customer.id,
                    await listCustomerLocations(customer.id, true),
                ] as const),
            );

            setCustomers(customerData);
            setCustomerLocations(Object.fromEntries(locationEntries));
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
        setInvoiceTitle("");
        setInvoiceDescription("");
        setCustomerId("");
        setLocationId("");
        setCreateLineItems([{ productId: "", quantity: "1", unitCostDollars: "", unitPriceDollars: "" }]);
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

            let unitCostCents: number | null = null;
            if (item.unitCostDollars.trim()) {
                try {
                    unitCostCents = dollarsToCents(item.unitCostDollars);
                } catch (err) {
                    setError(err instanceof Error ? err.message : "Enter a valid unit cost.");
                    return;
                }
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
                unit_cost_cents: unitCostCents,
                unit_price_cents: unitPriceCents,
            });
        }

        try {
            setIsSubmitting(true);
            setError(null);

            const invoice = await createInvoice({
                customer_id: Number(customerId),
                location_id: locationId ? Number(locationId) : null,
                title: invoiceTitle.trim() || null,
                description: invoiceDescription.trim() || null,
                date_issued: null,
                date_due: null,
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

	    async function handleActivateTag(tagId: number) {
	        try {
	            setError(null);
	            await updateTag(tagId, { is_active: true });
	            await loadData();
	        } catch (err) {
	            setError(err instanceof Error ? err.message : "Failed to activate tag.");
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

    function getLocationsForCustomer(selectedCustomerId: string) {
        const parsedCustomerId = Number(selectedCustomerId);
        if (!parsedCustomerId) {
            return [];
        }
        return customerLocations[parsedCustomerId] ?? [];
    }

    function formatCustomerLocation(location: CustomerLocation) {
        const addressLine2 = location.address_line2 ? `, ${location.address_line2}` : "";
        return `${location.address_line1}${addressLine2}, ${location.city}, ${location.state} ${location.postal_code}`;
    }

    function getLocationLabel(invoice: Invoice) {
        if (!invoice.location_id) {
            return "-";
        }

        const location = (customerLocations[invoice.customer_id] ?? []).find(
            (customerLocation) => customerLocation.id === invoice.location_id,
        );
        return location ? formatCustomerLocation(location) : `Location #${invoice.location_id}`;
    }

    function addCreateLineItem() {
        setCreateLineItems((current) => [
            ...current,
            { productId: "", quantity: "1", unitCostDollars: "", unitPriceDollars: "" },
        ]);
    }

    function selectCreateLineItemProduct(index: number, productId: string) {
        const product = products.find((candidate) => candidate.id === Number(productId));
        updateCreateLineItem(index, {
            productId,
            unitCostDollars: product ? centsToDollars(product.cost_cents) : "",
            unitPriceDollars: product ? centsToDollars(product.unit_price_cents) : "",
        });
    }

    function getAvailableProductsForCreateLineItem(index: number) {
        const selectedProductIds = new Set(
            createLineItems
                .map((lineItem, lineItemIndex) => lineItemIndex === index ? "" : lineItem.productId)
                .filter(Boolean),
        );

        return products.filter((product) => !selectedProductIds.has(String(product.id)));
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
                ? [{ productId: "", quantity: "1", unitCostDollars: "", unitPriceDollars: "" }]
                : current.filter((_, itemIndex) => itemIndex !== index)
        );
    }

    function isInteractiveTarget(target: EventTarget | null) {
        return target instanceof HTMLElement && Boolean(target.closest("button, input, select, textarea, a"));
    }

    function openInvoiceDetail(invoiceId: number) {
        navigate(`/invoices/${invoiceId}`);
    }

    function openTagDetail(tagId: number) {
        navigate(`/tags/${tagId}`);
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

    function handleTagRowClick(event: MouseEvent<HTMLTableRowElement>, tagId: number) {
        if (isInteractiveTarget(event.target)) {
            return;
        }

        openTagDetail(tagId);
    }

    function handleTagRowKeyDown(event: KeyboardEvent<HTMLTableRowElement>, tagId: number) {
        if (isInteractiveTarget(event.target)) {
            return;
        }

        if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            openTagDetail(tagId);
        }
    }

    return (
        <>
            <div className="page-header">
                <h2>Invoices</h2>
                <p>Create draft invoices and manage line items.</p>
            </div>

            <section className="invoice-page-stack">
                {error && <p className="error-message">{error}</p>}

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
                            className="form-card modal-panel invoice-modal-panel"
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
                                    <label htmlFor="invoice-title">Title</label>
                                    <input
                                        id="invoice-title"
                                        type="text"
                                        value={invoiceTitle}
                                        onChange={(event) => setInvoiceTitle(event.target.value)}
                                        placeholder="Mini split install"
                                    />
                                </div>

                                <div className="form-field">
                                    <label htmlFor="invoice-description">Description</label>
                                    <textarea
                                        id="invoice-description"
                                        value={invoiceDescription}
                                        onChange={(event) => setInvoiceDescription(event.target.value)}
                                        rows={3}
                                        placeholder="Describe the work performed"
                                    />
                                </div>

                                <div className="form-field">
                                    <label htmlFor="customer">Customer</label>
                                    <select
                                        id="customer"
                                        value={customerId}
                                        onChange={(event) => {
                                            setCustomerId(event.target.value);
                                            setLocationId("");
                                        }}
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
                                    <label htmlFor="invoice-location">Location</label>
                                    <select
                                        id="invoice-location"
                                        value={locationId}
                                        onChange={(event) => setLocationId(event.target.value)}
                                        disabled={!customerId}
                                    >
                                        <option value="">No location</option>
                                        {getLocationsForCustomer(customerId).map((location) => (
                                            <option key={location.id} value={location.id}>
                                                {formatCustomerLocation(location)}
                                            </option>
                                        ))}
                                    </select>
                                </div>

                                <div className="form-field invoice-line-items-field">
                                    <div className="invoice-items-panel">
                                        <div className="invoice-items-panel-header">
                                            <label>Line Items</label>
                                            <span>{createLineItems.length} item{createLineItems.length === 1 ? "" : "s"}</span>
                                        </div>
                                        <div className="line-item-list">
                                        {createLineItems.map((item, index) => (
                                            <div className="invoice-line-item-card" key={index}>
                                                <div className="line-item-control product-control">
                                                    <span>Product</span>
                                                    <select
                                                        aria-label={`Product for new invoice item ${index + 1}`}
                                                        value={item.productId}
                                                        onChange={(event) => selectCreateLineItemProduct(index, event.target.value)}
                                                    >
                                                        <option value="">Select product</option>
                                                        {getAvailableProductsForCreateLineItem(index).map((product) => (
                                                            <option key={product.id} value={product.id}>
                                                                {product.name} - ${centsToDollars(product.unit_price_cents)}
                                                            </option>
                                                        ))}
                                                    </select>
                                                </div>
                                                <div className="line-item-control quantity-control">
                                                    <span>Qty</span>
                                                    <input
                                                        aria-label={`Quantity for new invoice item ${index + 1}`}
                                                        type="number"
                                                        min="1"
                                                        value={item.quantity}
                                                        onChange={(event) => updateCreateLineItem(index, { quantity: event.target.value })}
                                                        disabled={!item.productId}
                                                    />
                                                </div>
                                                <div className="line-item-control money-control">
                                                    <span>Unit Cost</span>
                                                    <div className="currency-input">
                                                        <span aria-hidden="true">$</span>
                                                        <input
                                                            aria-label={`Unit cost for new invoice item ${index + 1}`}
                                                            type="text"
                                                            value={item.unitCostDollars}
                                                            onChange={(event) => updateCreateLineItem(index, { unitCostDollars: event.target.value })}
                                                            placeholder="0"
                                                            disabled={!item.productId}
                                                        />
                                                    </div>
                                                </div>
                                                <div className="line-item-control money-control">
                                                    <span>Unit Price</span>
                                                    <div className="currency-input">
                                                        <span aria-hidden="true">$</span>
                                                        <input
                                                            aria-label={`Unit price for new invoice item ${index + 1}`}
                                                            type="text"
                                                            value={item.unitPriceDollars}
                                                            onChange={(event) => updateCreateLineItem(index, { unitPriceDollars: event.target.value })}
                                                            placeholder="0"
                                                            disabled={!item.productId}
                                                        />
                                                    </div>
                                                </div>
                                                <div className="line-item-actions">
                                                    <button
                                                        className="small-danger-button"
                                                        type="button"
                                                        onClick={() => removeCreateLineItem(index)}
                                                    >
                                                        Remove
                                                    </button>
                                                </div>
                                            </div>
                                        ))}
                                        </div>
                                        <div className="additional-items-row">
                                            <span>Additional Items</span>
                                            <button className="small-action-button" type="button" onClick={addCreateLineItem}>
                                                Add Item
                                            </button>
                                        </div>
                                    </div>
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
	                    <>
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
	                                            <th>Primary Location</th>
	                                            <th>Date Due</th>
	                                            <th>Total</th>
	                                            <th>Status</th>
	                                            <th>Actions</th>
	                                        </tr>
	                                    </thead>

	                                    <tbody>
	                                        {invoices.map((invoice) => (
	                                            <tr
	                                                key={invoice.id}
	                                                className="clickable-row"
	                                                tabIndex={0}
	                                                aria-label={`View invoice ${invoice.id}`}
	                                                onClick={(event) => handleInvoiceRowClick(event, invoice.id)}
	                                                onKeyDown={(event) => handleInvoiceRowKeyDown(event, invoice.id)}
	                                            >
	                                                <td>{invoice.id}</td>
	                                                <td>{getCustomerName(invoice.customer_id)}</td>
	                                                <td>{getLocationLabel(invoice)}</td>
	                                                <td>{formatDisplayDate(invoice.date_due)}</td>
	                                                <td>${centsToDollars(invoice.total)}</td>
	                                                <td>
	                                                    <span className="status-badge">{invoice.status}</span>
	                                                </td>
	                                                <td>
	                                                    <button
	                                                        className="small-danger-button"
	                                                        type="button"
	                                                        onClick={() => handleDeleteInvoice(invoice.id)}
	                                                    >
	                                                        Delete
	                                                    </button>
	                                                </td>
	                                            </tr>
	                                        ))}
	                                    </tbody>
	                                </table>
	                            )}
	                        </div>
	                        <div className="invoice-assistant-below-list">
	                            <AssistantChatBox />
	                        </div>
	                    </>
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
                                            <tr
                                                key={tag.id}
                                                className={editingTagId === tag.id ? undefined : "clickable-row"}
                                                tabIndex={editingTagId === tag.id ? undefined : 0}
                                                aria-label={editingTagId === tag.id ? undefined : `View tag ${tag.name}`}
                                                onClick={editingTagId === tag.id ? undefined : (event) => handleTagRowClick(event, tag.id)}
                                                onKeyDown={editingTagId === tag.id ? undefined : (event) => handleTagRowKeyDown(event, tag.id)}
                                            >
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
	                                                                {!tag.is_active && (
	                                                                    <button className="small-action-button" type="button" onClick={() => handleActivateTag(tag.id)}>
	                                                                        Activate
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
