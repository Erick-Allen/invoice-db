import { useEffect, useMemo, useRef, useState, type KeyboardEvent, type SubmitEventHandler } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import {
    createCustomerLocation,
    deleteCustomerLocation,
    getCustomer,
    listCustomerLocations,
    listLocations,
    updateCustomer,
    updateCustomerLocation,
    type Customer,
    type CustomerLocation,
    type Location,
} from "../api/customers";
import { createInvoice, listInvoices, type Invoice, type InvoiceStatus } from "../api/invoices";
import { getPaymentSummary, type PaymentSummary } from "../api/payments";
import { formatDisplayDate } from "../utils/date";
import { centsToDollars } from "../utils/money";
import { digitsOnly, formatPhoneNumber, isValidCustomerPhone } from "../utils/phone";

type StatusCounts = Record<InvoiceStatus, number>;

type CustomerDetailLocationState = {
    fromInvoiceId?: number;
};

const EMPTY_STATUS_COUNTS: StatusCounts = {
    draft: 0,
    sent: 0,
    paid: 0,
    void: 0,
};

const INVOICE_STATUS_FILTERS: Array<InvoiceStatus | "all"> = ["all", "draft", "sent", "paid", "void"];

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

function formatAddress(address: Pick<CustomerLocation | Location, "address_line1" | "address_line2" | "city" | "state" | "postal_code">) {
    const line2 = address.address_line2 ? `, ${address.address_line2}` : "";
    return `${address.address_line1}${line2}, ${address.city}, ${address.state} ${address.postal_code}`;
}

function formatCurrency(cents: number) {
    return cents < 0 ? `-$${centsToDollars(Math.abs(cents))}` : `$${centsToDollars(cents)}`;
}

export function CustomerDetailPage() {
    const { customerId } = useParams();
    const location = useLocation();
    const navigate = useNavigate();
    const invoiceHistoryRef = useRef<HTMLElement | null>(null);
    const [customer, setCustomer] = useState<Customer | null>(null);
    const [locations, setLocations] = useState<CustomerLocation[]>([]);
    const [invoices, setInvoices] = useState<Invoice[]>([]);
    const [paymentSummaries, setPaymentSummaries] = useState<Record<number, PaymentSummary>>({});
    const [isCustomerEditing, setIsCustomerEditing] = useState(false);
    const [isCustomerSubmitting, setIsCustomerSubmitting] = useState(false);
    const [editCustomerName, setEditCustomerName] = useState("");
    const [editCustomerEmail, setEditCustomerEmail] = useState("");
    const [editCustomerPhone, setEditCustomerPhone] = useState("");
    const [editCustomerType, setEditCustomerType] = useState<Customer["customer_type"]>("residential");
    const [editCustomerCompanyName, setEditCustomerCompanyName] = useState("");
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [isCreateInvoiceOpen, setIsCreateInvoiceOpen] = useState(false);
    const [isCreateInvoiceSubmitting, setIsCreateInvoiceSubmitting] = useState(false);
    const [invoiceTitle, setInvoiceTitle] = useState("");
    const [invoiceDescription, setInvoiceDescription] = useState("");
    const [invoiceLocationId, setInvoiceLocationId] = useState("");
    const [invoiceDateIssued, setInvoiceDateIssued] = useState("");
    const [invoiceDateDue, setInvoiceDateDue] = useState("");
    const [availableLocations, setAvailableLocations] = useState<Location[]>([]);
    const [isAddLocationOpen, setIsAddLocationOpen] = useState(false);
    const [isAddLocationSubmitting, setIsAddLocationSubmitting] = useState(false);
    const [addLocationMode, setAddLocationMode] = useState<"new" | "existing">("new");
    const [addExistingLocationId, setAddExistingLocationId] = useState("");
    const [addLocationLabel, setAddLocationLabel] = useState("");
    const [addLocationAddressLine1, setAddLocationAddressLine1] = useState("");
    const [addLocationAddressLine2, setAddLocationAddressLine2] = useState("");
    const [addLocationCity, setAddLocationCity] = useState("");
    const [addLocationStateInput, setAddLocationStateInput] = useState("");
    const [addLocationPostalCode, setAddLocationPostalCode] = useState("");
    const [addLocationNotes, setAddLocationNotes] = useState("");
    const [addLocationIsPrimary, setAddLocationIsPrimary] = useState(false);
    const [editingLocation, setEditingLocation] = useState<CustomerLocation | null>(null);
    const [editLocationLabel, setEditLocationLabel] = useState("");
    const [editLocationAddressLine1, setEditLocationAddressLine1] = useState("");
    const [editLocationAddressLine2, setEditLocationAddressLine2] = useState("");
    const [editLocationCity, setEditLocationCity] = useState("");
    const [editLocationStateInput, setEditLocationStateInput] = useState("");
    const [editLocationPostalCode, setEditLocationPostalCode] = useState("");
    const [editLocationNotes, setEditLocationNotes] = useState("");
    const [editLocationIsPrimary, setEditLocationIsPrimary] = useState(false);
    const [editLocationIsActive, setEditLocationIsActive] = useState(true);
    const [isEditLocationSubmitting, setIsEditLocationSubmitting] = useState(false);
    const [invoiceStatusFilter, setInvoiceStatusFilter] = useState<InvoiceStatus | "all">("all");
    const locationState = location.state as CustomerDetailLocationState | null;
    const backTarget = locationState?.fromInvoiceId ? `/invoices/${locationState.fromInvoiceId}` : "/customers";
    const backLabel = locationState?.fromInvoiceId ? "Back to invoice" : "Back to customers";

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

                const [customerData, invoiceData, locationData] = await Promise.all([
                    getCustomer(parsedCustomerId),
                    listInvoices({ customerId: parsedCustomerId, includeItems: true }),
                    listCustomerLocations(parsedCustomerId),
                ]);
                const paymentSummaryEntries = await Promise.all(
                    invoiceData.map(async (invoice) => [
                        invoice.id,
                        await getPaymentSummary(invoice.id),
                    ] as const)
                );

                setCustomer(customerData);
                setLocations(locationData);
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

    function openLocationDetail(locationId: number) {
        navigate(`/locations/${locationId}`, { state: { fromCustomerId: customer?.id } });
    }

    function startEditingCustomer() {
        if (!customer) {
            return;
        }

        setError(null);
        setEditCustomerName(customer.name);
        setEditCustomerEmail(customer.email);
        setEditCustomerPhone(customer.phone ?? "");
        setEditCustomerType(customer.customer_type ?? "residential");
        setEditCustomerCompanyName(customer.company_name ?? "");
        setIsCustomerEditing(true);
    }

    function cancelEditingCustomer() {
        if (isCustomerSubmitting) {
            return;
        }

        setIsCustomerEditing(false);
        setEditCustomerName("");
        setEditCustomerEmail("");
        setEditCustomerPhone("");
        setEditCustomerType("residential");
        setEditCustomerCompanyName("");
    }

    function revealInvoiceHistory(statusFilter: InvoiceStatus | "all" = "all") {
        setInvoiceStatusFilter(statusFilter);
        invoiceHistoryRef.current?.scrollIntoView?.({ behavior: "smooth", block: "start" });
    }

    function openCreateInvoice() {
        setError(null);
        setIsCreateInvoiceOpen(true);
    }

    function resetCreateInvoiceForm() {
        setInvoiceTitle("");
        setInvoiceDescription("");
        setInvoiceLocationId("");
        setInvoiceDateIssued("");
        setInvoiceDateDue("");
    }

    function closeCreateInvoice() {
        if (isCreateInvoiceSubmitting) {
            return;
        }

        resetCreateInvoiceForm();
        setIsCreateInvoiceOpen(false);
    }

    function resetAddLocationForm() {
        setAddLocationMode("new");
        setAddExistingLocationId("");
        setAddLocationLabel("");
        setAddLocationAddressLine1("");
        setAddLocationAddressLine2("");
        setAddLocationCity("");
        setAddLocationStateInput("");
        setAddLocationPostalCode("");
        setAddLocationNotes("");
        setAddLocationIsPrimary(false);
    }

    async function openAddLocation() {
        try {
            setError(null);
            setAvailableLocations(await listLocations());
            setIsAddLocationOpen(true);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to load available locations.");
        }
    }

    function closeAddLocation() {
        if (isAddLocationSubmitting) {
            return;
        }

        resetAddLocationForm();
        setIsAddLocationOpen(false);
    }

    function openEditLocation(location: CustomerLocation) {
        setError(null);
        setEditingLocation(location);
        setEditLocationLabel(location.label);
        setEditLocationAddressLine1(location.address_line1);
        setEditLocationAddressLine2(location.address_line2 ?? "");
        setEditLocationCity(location.city);
        setEditLocationStateInput(location.state);
        setEditLocationPostalCode(location.postal_code);
        setEditLocationNotes(location.notes ?? "");
        setEditLocationIsPrimary(location.is_primary);
        setEditLocationIsActive(location.is_active);
    }

    function closeEditLocation() {
        if (isEditLocationSubmitting) {
            return;
        }

        setEditingLocation(null);
    }

    async function refreshLocations(customerIdToRefresh: number) {
        const locationData = await listCustomerLocations(customerIdToRefresh);
        setLocations(locationData);
    }

    const activeLocations = locations.filter((location) => location.is_active);

    const handleUpdateCustomer: SubmitEventHandler<HTMLFormElement> = async (event) => {
        event.preventDefault();

        if (!customer) {
            return;
        }

        const trimmedName = editCustomerName.trim();
        const trimmedEmail = editCustomerEmail.trim();

        if (!trimmedName) {
            setError("Customer name is required.");
            return;
        }

        if (!trimmedEmail) {
            setError("Customer email is required.");
            return;
        }

        if (!isValidCustomerPhone(editCustomerPhone)) {
            setError("Customer phone must be exactly 10 digits.");
            return;
        }

        try {
            setIsCustomerSubmitting(true);
            setError(null);
            const updatedCustomer = await updateCustomer(customer.id, {
                name: trimmedName,
                email: trimmedEmail,
                phone: editCustomerPhone.trim() || null,
                customer_type: editCustomerType,
                company_name: editCustomerType === "residential" ? null : editCustomerCompanyName.trim() || null,
            });
            setCustomer(updatedCustomer);
            setIsCustomerEditing(false);
            setEditCustomerName("");
            setEditCustomerEmail("");
            setEditCustomerPhone("");
            setEditCustomerType("residential");
            setEditCustomerCompanyName("");
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to update customer.");
        } finally {
            setIsCustomerSubmitting(false);
        }
    };

    const handleCreateInvoice: SubmitEventHandler<HTMLFormElement> = async (event) => {
        event.preventDefault();

        if (!customer) {
            return;
        }

        try {
            setIsCreateInvoiceSubmitting(true);
            setError(null);
            const invoice = await createInvoice({
                customer_id: customer.id,
                location_id: invoiceLocationId ? Number(invoiceLocationId) : null,
                title: invoiceTitle.trim() || null,
                description: invoiceDescription.trim() || null,
                date_issued: invoiceDateIssued || null,
                date_due: invoiceDateDue || null,
            });
            resetCreateInvoiceForm();
            setIsCreateInvoiceOpen(false);
            navigate(`/invoices/${invoice.id}`, { state: { fromCustomerId: customer.id } });
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to create invoice.");
        } finally {
            setIsCreateInvoiceSubmitting(false);
        }
    };

    const assignableLocations = availableLocations.filter(
        (availableLocation) => !locations.some((location) => location.location_id === availableLocation.id)
    );

    const handleAddLocation: SubmitEventHandler<HTMLFormElement> = async (event) => {
        event.preventDefault();

        if (!customer) {
            return;
        }

        const selectedExistingLocation = assignableLocations.find(
            (location) => location.id === Number(addExistingLocationId)
        );

        if (addLocationMode === "existing" && !selectedExistingLocation) {
            setError("Existing location is required.");
            return;
        }

        if (
            addLocationMode === "new" &&
            (!addLocationLabel.trim() || !addLocationAddressLine1.trim() || !addLocationCity.trim() || !addLocationStateInput.trim() || !addLocationPostalCode.trim())
        ) {
            setError("Location label, address, city, state, and ZIP code are required.");
            return;
        }

        const nextLabel = addLocationLabel.trim() || "Location";
        const nextAddressLine1 = addLocationMode === "existing" ? selectedExistingLocation?.address_line1 ?? "" : addLocationAddressLine1.trim();
        const nextAddressLine2 = addLocationMode === "existing" ? selectedExistingLocation?.address_line2 ?? null : addLocationAddressLine2.trim() || null;
        const nextCity = addLocationMode === "existing" ? selectedExistingLocation?.city ?? "" : addLocationCity.trim();
        const nextState = addLocationMode === "existing" ? selectedExistingLocation?.state ?? "" : addLocationStateInput.trim();
        const nextPostalCode = addLocationMode === "existing" ? selectedExistingLocation?.postal_code ?? "" : addLocationPostalCode.trim();
        const nextCountry = addLocationMode === "existing" ? selectedExistingLocation?.country ?? "US" : "US";

        try {
            setIsAddLocationSubmitting(true);
            setError(null);
            await createCustomerLocation(customer.id, {
                label: nextLabel,
                address_line1: nextAddressLine1,
                address_line2: nextAddressLine2,
                city: nextCity,
                state: nextState,
                postal_code: nextPostalCode,
                country: nextCountry,
                is_primary: addLocationIsPrimary,
                notes: addLocationNotes.trim() || null,
            });
            resetAddLocationForm();
            setIsAddLocationOpen(false);
            await refreshLocations(customer.id);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to add customer location.");
        } finally {
            setIsAddLocationSubmitting(false);
        }
    };

    const handleUpdateLocation: SubmitEventHandler<HTMLFormElement> = async (event) => {
        event.preventDefault();

        if (!customer || !editingLocation) {
            return;
        }

        if (!editLocationLabel.trim() || !editLocationAddressLine1.trim() || !editLocationCity.trim() || !editLocationStateInput.trim() || !editLocationPostalCode.trim()) {
            setError("Location label, address, city, state, and ZIP code are required.");
            return;
        }

        try {
            setIsEditLocationSubmitting(true);
            setError(null);
            await updateCustomerLocation(customer.id, editingLocation.id, {
                label: editLocationLabel.trim(),
                address_line1: editLocationAddressLine1.trim(),
                address_line2: editLocationAddressLine2.trim() || null,
                city: editLocationCity.trim(),
                state: editLocationStateInput.trim(),
                postal_code: editLocationPostalCode.trim(),
                country: editingLocation.country || "US",
                is_primary: editLocationIsPrimary,
                is_active: editLocationIsActive,
                notes: editLocationNotes.trim() || null,
            });
            setEditingLocation(null);
            await refreshLocations(customer.id);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to update customer location.");
        } finally {
            setIsEditLocationSubmitting(false);
        }
    };

	    async function handleRemoveLocation(locationId: number) {
	        if (!customer) {
	            return;
	        }

        const confirmed = window.confirm("Remove this location from the customer?");
        if (!confirmed) {
            return;
        }

        try {
            setError(null);
            await deleteCustomerLocation(customer.id, locationId);
            await refreshLocations(customer.id);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to remove customer location.");
	        }
	    }

	    async function handleActivateLocation(location: CustomerLocation) {
	        if (!customer) {
	            return;
	        }

	        try {
	            setError(null);
	            await updateCustomerLocation(customer.id, location.id, { is_active: true });
	            await refreshLocations(customer.id);
	        } catch (err) {
	            setError(err instanceof Error ? err.message : "Failed to activate customer location.");
	        }
	    }

    function formatLocation(location: CustomerLocation) {
        return formatAddress(location);
    }

    function getInvoiceLocationLabel(invoice: Invoice) {
        if (!invoice.location_id) {
            return "-";
        }

        const location = locations.find((customerLocation) => customerLocation.id === invoice.location_id);
        return location ? location.label : `Location #${invoice.location_id}`;
    }

    function handleInvoiceRowKeyDown(event: KeyboardEvent<HTMLTableRowElement>, invoiceId: number) {
        if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            openInvoiceDetail(invoiceId);
        }
    }

    function handleLocationRowKeyDown(event: KeyboardEvent<HTMLTableRowElement>, locationId: number) {
        if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            openLocationDetail(locationId);
        }
    }

    const summary = useMemo(() => {
        const totals = invoices.reduce(
            (current, invoice) => {
                const paymentSummary = paymentSummaries[invoice.id];
                const isIssuedInvoice = invoice.status === "sent" || invoice.status === "paid";

                if (isIssuedInvoice) {
                    current.totalInvoicedCents += invoice.total;
                    current.totalCostCents += invoice.cost_total_cents ?? 0;
                }
                current.totalPaidCents += paymentSummary?.amount_paid_cents ?? 0;
                if (invoice.status === "sent") {
                    current.totalOwedCents += paymentSummary?.balance_due_cents ?? invoice.total;
                }
                current.statusCounts[invoice.status] += 1;

                return current;
            },
            {
                totalInvoicedCents: 0,
                totalPaidCents: 0,
                totalCostCents: 0,
                totalProfitCents: 0,
                totalOwedCents: 0,
                statusCounts: { ...EMPTY_STATUS_COUNTS },
            }
        );

        return {
            ...totals,
            totalProfitCents: totals.totalPaidCents - totals.totalCostCents,
        };
    }, [invoices, paymentSummaries]);

    const filteredInvoices = useMemo(() => {
        if (invoiceStatusFilter === "all") {
            return invoices;
        }

        return invoices.filter((invoice) => invoice.status === invoiceStatusFilter);
    }, [invoiceStatusFilter, invoices]);

    return (
        <>
            <div className="page-header">
                <Link className="back-link" to={backTarget}>
                    {backLabel}
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
                        <div className="section-header">
                            <div>
                                <span className="detail-label">Customer</span>
                                <h3>{customer.name}</h3>
                            </div>
                            {!isCustomerEditing && (
                                <button className="small-action-button" type="button" onClick={startEditingCustomer}>
                                    Edit
                                </button>
                            )}
                        </div>

	                        {isCustomerEditing ? (
	                            <form className="form-grid" onSubmit={handleUpdateCustomer} noValidate>
                                <div className="form-field">
                                    <label htmlFor="customer-detail-name">Name</label>
                                    <input
                                        id="customer-detail-name"
                                        type="text"
                                        value={editCustomerName}
                                        onChange={(event) => setEditCustomerName(event.target.value)}
                                    />
                                </div>
                                <div className="form-field">
                                    <label htmlFor="customer-detail-email">Email</label>
                                    <input
                                        id="customer-detail-email"
                                        type="email"
                                        value={editCustomerEmail}
                                        onChange={(event) => setEditCustomerEmail(event.target.value)}
                                    />
                                </div>
                                <div className="form-field">
                                    <label htmlFor="customer-detail-phone">Phone</label>
                                    <input
	                                        id="customer-detail-phone"
	                                        type="text"
	                                        inputMode="numeric"
	                                        pattern="[0-9]{10}"
	                                        maxLength={10}
	                                        value={editCustomerPhone}
	                                        onChange={(event) => setEditCustomerPhone(digitsOnly(event.target.value).slice(0, 10))}
	                                    />
                                </div>
                                <div className="form-field">
                                    <label htmlFor="customer-detail-type">Type</label>
                                    <select
                                        id="customer-detail-type"
                                        value={editCustomerType}
                                        onChange={(event) => {
                                            const nextType = event.target.value as Customer["customer_type"];
                                            setEditCustomerType(nextType);
                                            if (nextType === "residential") {
                                                setEditCustomerCompanyName("");
                                            }
                                        }}
                                    >
                                        <option value="residential">Residential</option>
                                        <option value="commercial">Commercial</option>
                                        <option value="property_manager">Property Manager</option>
                                        <option value="other">Other</option>
                                    </select>
                                </div>
                                {editCustomerType !== "residential" && (
                                    <div className="form-field">
                                        <label htmlFor="customer-detail-company">Company</label>
                                        <input
                                            id="customer-detail-company"
                                            type="text"
                                            value={editCustomerCompanyName}
                                            onChange={(event) => setEditCustomerCompanyName(event.target.value)}
                                        />
                                    </div>
                                )}
                                <div className="modal-actions">
                                    <button className="secondary-button" type="button" onClick={cancelEditingCustomer} disabled={isCustomerSubmitting}>
                                        Cancel
                                    </button>
                                    <button className="primary-button" type="submit" disabled={isCustomerSubmitting}>
                                        {isCustomerSubmitting ? "Saving..." : "Save"}
                                    </button>
                                </div>
                            </form>
                        ) : (
                            <dl className="detail-grid">
                                <div>
                                    <dt>Email</dt>
                                    <dd>{customer.email}</dd>
                                </div>
	                                <div>
	                                    <dt>Phone</dt>
	                                    <dd>{formatPhoneNumber(customer.phone)}</dd>
	                                </div>
                                <div>
                                    <dt>Type</dt>
                                    <dd>{customer.customer_type ?? "residential"}</dd>
                                </div>
                                {customer.company_name && (
                                    <div>
                                        <dt>Company</dt>
                                        <dd>{customer.company_name}</dd>
                                    </div>
                                )}
                                <div>
                                    <dt>Customer ID</dt>
                                    <dd>{customer.id}</dd>
                                </div>
                            </dl>
                        )}
                    </section>

                    <section className="detail-summary-grid" aria-label="Customer invoice summary">
                        <button className="summary-card-button" type="button" onClick={() => revealInvoiceHistory()}>
                            <span>Invoices</span>
                            <strong>{invoices.length}</strong>
                        </button>
                        <div>
                            <span>Total Invoiced</span>
                            <strong>{formatCurrency(summary.totalInvoicedCents)}</strong>
                        </div>
                        <div>
                            <span>Total Cost</span>
                            <strong>{formatCurrency(summary.totalCostCents)}</strong>
                        </div>
                        <button className="summary-card-button" type="button" onClick={() => revealInvoiceHistory("paid")}>
                            <span>Total Paid</span>
                            <strong>{formatCurrency(summary.totalPaidCents)}</strong>
                        </button>
                        <div>
                            <span>Net Profit</span>
                            <strong>{formatCurrency(summary.totalProfitCents)}</strong>
                        </div>
                        <button className="summary-card-button" type="button" onClick={() => revealInvoiceHistory("sent")}>
                            <span>Total Owed</span>
                            <strong>{formatCurrency(summary.totalOwedCents)}</strong>
                        </button>
                    </section>

                    <section className="detail-panel">
                        <div className="section-header">
                            <h3>Locations</h3>
                            <div className="section-actions">
                                <button className="primary-button" type="button" onClick={openAddLocation}>
                                    Add Location
                                </button>
                            </div>
                        </div>

                        {locations.length === 0 ? (
                            <p className="empty-state">No locations found for this customer.</p>
                        ) : (
                            <div className="table-wrapper detail-table-wrapper">
                                <table className="data-table">
                                    <thead>
                                        <tr>
                                            <th>Label</th>
                                            <th>Address</th>
                                            <th>Status</th>
                                            <th>Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {locations.map((location) => (
                                            <tr
                                                key={location.id}
                                                className="clickable-row"
                                                tabIndex={0}
                                                aria-label={`View location ${location.label}`}
                                                onClick={() => openLocationDetail(location.location_id)}
                                                onKeyDown={(event) => handleLocationRowKeyDown(event, location.location_id)}
                                            >
                                                <td>
                                                    <strong>{location.label}</strong>
                                                    {location.is_primary && <span className="status-badge">primary</span>}
                                                </td>
                                                <td>{formatLocation(location)}</td>
                                                <td><span className="status-badge">{location.is_active ? "active" : "inactive"}</span></td>
                                                <td>
                                                    <div className="table-actions">
	                                                        <button
	                                                            className="small-action-button"
	                                                            type="button"
                                                            onClick={(event) => {
                                                                event.stopPropagation();
                                                                openEditLocation(location);
                                                            }}
                                                        >
	                                                            Edit
	                                                        </button>
	                                                        {!location.is_active && (
	                                                            <button
	                                                                className="small-action-button"
	                                                                type="button"
	                                                                onClick={(event) => {
	                                                                    event.stopPropagation();
	                                                                    handleActivateLocation(location);
	                                                                }}
	                                                            >
	                                                                Activate
	                                                            </button>
	                                                        )}
	                                                        <button
                                                            className="small-danger-button"
                                                            type="button"
                                                            onClick={(event) => {
                                                                event.stopPropagation();
                                                                handleRemoveLocation(location.id);
                                                            }}
                                                        >
                                                            Remove
                                                        </button>
                                                    </div>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </section>

                    <section className="detail-panel" ref={invoiceHistoryRef}>
                        <div className="section-header">
                            <h3>Invoice History</h3>
                            <div className="section-actions">
                                <button className="primary-button" type="button" onClick={openCreateInvoice}>
                                    Create New Invoice
                                </button>
                            </div>
                        </div>

                        {invoices.length > 0 && (
                            <div className="segmented-tabs detail-filter-tabs" role="tablist" aria-label="Invoice status filters">
                                {INVOICE_STATUS_FILTERS.map((status) => {
                                    const count = status === "all" ? invoices.length : summary.statusCounts[status];
                                    const label = status === "all" ? "All" : status;

                                    return (
                                        <button
                                            key={status}
                                            type="button"
                                            className={invoiceStatusFilter === status ? "active" : ""}
                                            onClick={() => setInvoiceStatusFilter(status)}
                                        >
                                            {label} ({count})
                                        </button>
                                    );
                                })}
                            </div>
                        )}

                        {invoices.length === 0 ? (
                            <p className="empty-state">No invoices found for this customer.</p>
                        ) : filteredInvoices.length === 0 ? (
                            <p className="empty-state">No {invoiceStatusFilter} invoices found for this customer.</p>
                        ) : (
                            <div className="table-wrapper detail-table-wrapper">
                                <table className="data-table">
                                    <thead>
                                        <tr>
                                            <th>Invoice</th>
                                            <th>Location</th>
                                            <th>Issued</th>
                                            <th>Due</th>
                                            <th>Status</th>
                                            <th>Total</th>
                                            <th>Paid</th>
                                            <th>Owed</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {filteredInvoices.map((invoice) => {
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
                                                    <td>{getInvoiceLocationLabel(invoice)}</td>
                                                    <td>{formatDisplayDate(invoice.date_issued)}</td>
                                                    <td>{formatDisplayDate(invoice.date_due)}</td>
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

            {isCreateInvoiceOpen && customer && (
                <div className="modal-overlay" role="presentation" onMouseDown={closeCreateInvoice}>
                    <form
                        className="form-card modal-panel"
                        role="dialog"
                        aria-modal="true"
                        aria-labelledby="create-customer-invoice-title"
                        onSubmit={handleCreateInvoice}
                        onMouseDown={(event) => event.stopPropagation()}
                    >
                        <div className="modal-header">
                            <h3 id="create-customer-invoice-title">Create Invoice</h3>
                            <button className="icon-button" type="button" aria-label="Close create invoice" onClick={closeCreateInvoice}>
                                x
                            </button>
                        </div>

                        <div className="form-grid modal-form-grid">
                            <div className="form-field">
                                <label htmlFor="invoice-customer">Customer</label>
                                <input id="invoice-customer" type="text" value={`${customer.name} - ${customer.email}`} disabled />
                            </div>
                            <div className="form-field">
                                <label htmlFor="customer-invoice-title">Title</label>
                                <input
                                    id="customer-invoice-title"
                                    type="text"
                                    value={invoiceTitle}
                                    onChange={(event) => setInvoiceTitle(event.target.value)}
                                    placeholder="Mini split install"
                                />
                            </div>
                            <div className="form-field">
                                <label htmlFor="customer-invoice-description">Description</label>
                                <textarea
                                    id="customer-invoice-description"
                                    value={invoiceDescription}
                                    onChange={(event) => setInvoiceDescription(event.target.value)}
                                    rows={3}
                                    placeholder="Describe the work performed"
                                />
                            </div>
                            <div className="form-field">
                                <label htmlFor="customer-invoice-location">Location</label>
                                <select
                                    id="customer-invoice-location"
                                    value={invoiceLocationId}
                                    onChange={(event) => setInvoiceLocationId(event.target.value)}
                                >
                                    <option value="">No location</option>
                                    {activeLocations.map((location) => (
                                        <option key={location.id} value={location.id}>
                                            {location.label}
                                        </option>
                                    ))}
                                </select>
                            </div>
                            <div className="form-field">
                                <label htmlFor="customer-invoice-date-issued">Date Issued</label>
                                <input
                                    id="customer-invoice-date-issued"
                                    type="date"
                                    value={invoiceDateIssued}
                                    onChange={(event) => setInvoiceDateIssued(event.target.value)}
                                />
                            </div>
                            <div className="form-field">
                                <label htmlFor="customer-invoice-date-due">Date Due</label>
                                <input
                                    id="customer-invoice-date-due"
                                    type="date"
                                    value={invoiceDateDue}
                                    onChange={(event) => setInvoiceDateDue(event.target.value)}
                                />
                            </div>
                            <div className="modal-actions">
                                <button className="secondary-button" type="button" onClick={closeCreateInvoice} disabled={isCreateInvoiceSubmitting}>
                                    Cancel
                                </button>
                                <button className="primary-button" type="submit" disabled={isCreateInvoiceSubmitting}>
                                    {isCreateInvoiceSubmitting ? "Creating..." : "Create Invoice"}
                                </button>
                            </div>
                        </div>
                    </form>
                </div>
            )}

            {isAddLocationOpen && (
                <div className="modal-overlay" role="presentation" onMouseDown={closeAddLocation}>
                    <form
                        className="form-card modal-panel"
                        role="dialog"
                        aria-modal="true"
                        aria-labelledby="add-location-title"
                        onSubmit={handleAddLocation}
                        onMouseDown={(event) => event.stopPropagation()}
                    >
                        <div className="modal-header">
                            <h3 id="add-location-title">Add Location</h3>
                            <button className="icon-button" type="button" aria-label="Close add location" onClick={closeAddLocation}>
                                x
                            </button>
                        </div>

                        <div className="form-grid modal-form-grid">
                            <div className="segmented-tabs" role="tablist" aria-label="Location source">
                                <button
                                    type="button"
                                    className={addLocationMode === "new" ? "active" : ""}
                                    onClick={() => setAddLocationMode("new")}
                                >
                                    New Address
                                </button>
                                <button
                                    type="button"
                                    className={addLocationMode === "existing" ? "active" : ""}
                                    onClick={() => setAddLocationMode("existing")}
                                >
                                    Existing Address
                                </button>
                            </div>

                            <div className="form-field">
                                <label htmlFor="add-location-label">Label</label>
                                <input
                                    id="add-location-label"
                                    value={addLocationLabel}
                                    onChange={(event) => setAddLocationLabel(event.target.value)}
                                    placeholder="Home"
                                />
                            </div>

                            {addLocationMode === "existing" ? (
                                <div className="form-field">
                                    <label htmlFor="add-existing-location">Existing Address</label>
                                    <select
                                        id="add-existing-location"
                                        value={addExistingLocationId}
                                        onChange={(event) => setAddExistingLocationId(event.target.value)}
                                    >
                                        <option value="">Select a location</option>
                                        {assignableLocations.map((location) => (
                                            <option key={location.id} value={location.id}>
                                                {formatAddress(location)}
                                            </option>
                                        ))}
                                    </select>
                                </div>
                            ) : (
                                <>
                                    <div className="form-field">
                                        <label htmlFor="add-location-address-line1">Address</label>
                                        <input id="add-location-address-line1" value={addLocationAddressLine1} onChange={(event) => setAddLocationAddressLine1(event.target.value)} placeholder="123 Main St" />
                                    </div>
                                    <div className="form-field">
                                        <label htmlFor="add-location-address-line2">Address 2</label>
                                        <input id="add-location-address-line2" value={addLocationAddressLine2} onChange={(event) => setAddLocationAddressLine2(event.target.value)} placeholder="Suite 200" />
                                    </div>
                                    <div className="form-field">
                                        <label htmlFor="add-location-city">City</label>
                                        <input id="add-location-city" value={addLocationCity} onChange={(event) => setAddLocationCity(event.target.value)} placeholder="Orlando" />
                                    </div>
                                    <div className="form-field">
                                        <label htmlFor="add-location-state">State</label>
                                        <input id="add-location-state" value={addLocationStateInput} onChange={(event) => setAddLocationStateInput(event.target.value)} placeholder="FL" />
                                    </div>
                                    <div className="form-field">
                                        <label htmlFor="add-location-postal-code">ZIP code</label>
                                        <input id="add-location-postal-code" value={addLocationPostalCode} onChange={(event) => setAddLocationPostalCode(event.target.value)} placeholder="32801" />
                                    </div>
                                </>
                            )}

                            <div className="form-field">
                                <label htmlFor="add-location-notes">Notes</label>
                                <input id="add-location-notes" value={addLocationNotes} onChange={(event) => setAddLocationNotes(event.target.value)} placeholder="Gate code, access notes" />
                            </div>
                            <label className="inline-toggle">
                                <input
                                    type="checkbox"
                                    checked={addLocationIsPrimary}
                                    onChange={(event) => setAddLocationIsPrimary(event.target.checked)}
                                />
                                Primary
                            </label>
                            <div className="modal-actions">
                                <button className="secondary-button" type="button" onClick={closeAddLocation} disabled={isAddLocationSubmitting}>
                                    Cancel
                                </button>
                                <button className="primary-button" type="submit" disabled={isAddLocationSubmitting}>
                                    {isAddLocationSubmitting ? "Adding..." : "Add Location"}
                                </button>
                            </div>
                        </div>
                    </form>
                </div>
            )}

            {editingLocation && (
                <div className="modal-overlay" role="presentation" onMouseDown={closeEditLocation}>
                    <form
                        className="form-card modal-panel"
                        role="dialog"
                        aria-modal="true"
                        aria-labelledby="edit-location-title"
                        onSubmit={handleUpdateLocation}
                        onMouseDown={(event) => event.stopPropagation()}
                    >
                        <div className="modal-header">
                            <h3 id="edit-location-title">Edit Location</h3>
                            <button className="icon-button" type="button" aria-label="Close edit location" onClick={closeEditLocation}>
                                x
                            </button>
                        </div>

                        <div className="form-grid modal-form-grid">
                            <div className="form-field">
                                <label htmlFor="edit-location-label">Label</label>
                                <input id="edit-location-label" value={editLocationLabel} onChange={(event) => setEditLocationLabel(event.target.value)} placeholder="Home" />
                            </div>
                            <div className="form-field">
                                <label htmlFor="edit-location-address-line1">Address</label>
                                <input id="edit-location-address-line1" value={editLocationAddressLine1} onChange={(event) => setEditLocationAddressLine1(event.target.value)} placeholder="123 Main St" />
                            </div>
                            <div className="form-field">
                                <label htmlFor="edit-location-address-line2">Address 2</label>
                                <input id="edit-location-address-line2" value={editLocationAddressLine2} onChange={(event) => setEditLocationAddressLine2(event.target.value)} placeholder="Suite 200" />
                            </div>
                            <div className="form-field">
                                <label htmlFor="edit-location-city">City</label>
                                <input id="edit-location-city" value={editLocationCity} onChange={(event) => setEditLocationCity(event.target.value)} placeholder="Orlando" />
                            </div>
                            <div className="form-field">
                                <label htmlFor="edit-location-state">State</label>
                                <input id="edit-location-state" value={editLocationStateInput} onChange={(event) => setEditLocationStateInput(event.target.value)} placeholder="FL" />
                            </div>
                            <div className="form-field">
                                <label htmlFor="edit-location-postal-code">ZIP code</label>
                                <input id="edit-location-postal-code" value={editLocationPostalCode} onChange={(event) => setEditLocationPostalCode(event.target.value)} placeholder="32801" />
                            </div>
                            <div className="form-field">
                                <label htmlFor="edit-location-notes">Notes</label>
                                <input id="edit-location-notes" value={editLocationNotes} onChange={(event) => setEditLocationNotes(event.target.value)} placeholder="Gate code, access notes" />
                            </div>
                            <label className="inline-toggle">
                                <input
                                    type="checkbox"
                                    checked={editLocationIsPrimary}
                                    onChange={(event) => setEditLocationIsPrimary(event.target.checked)}
                                />
                                Primary
                            </label>
                            <label className="inline-toggle">
                                <input
                                    type="checkbox"
                                    checked={editLocationIsActive}
                                    onChange={(event) => setEditLocationIsActive(event.target.checked)}
                                />
                                Active
                            </label>
                            <div className="modal-actions">
                                <button className="secondary-button" type="button" onClick={closeEditLocation} disabled={isEditLocationSubmitting}>
                                    Cancel
                                </button>
                                <button className="primary-button" type="submit" disabled={isEditLocationSubmitting}>
                                    {isEditLocationSubmitting ? "Saving..." : "Save Location"}
                                </button>
                            </div>
                        </div>
                    </form>
                </div>
            )}
        </>
    );
}
