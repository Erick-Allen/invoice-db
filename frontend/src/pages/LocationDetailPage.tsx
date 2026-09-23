import { useEffect, useState, type KeyboardEvent, type SubmitEventHandler } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import {
    createCustomerLocation,
    getLocation,
    listCustomers,
    updateLocation,
    type Customer,
    type LocationDetail,
} from "../api/customers";
import { createSupplierLocation, listSuppliers, type Supplier } from "../api/suppliers";
import { formatDisplayDate } from "../utils/date";
import { centsToDollars } from "../utils/money";

type LocationDetailLocationState = {
    fromCustomerId?: number;
    fromInvoiceId?: number;
};

export function LocationDetailPage() {
    const { locationId } = useParams();
    const location = useLocation();
    const navigate = useNavigate();
    const [detail, setDetail] = useState<LocationDetail | null>(null);
    const [customers, setCustomers] = useState<Customer[]>([]);
    const [suppliers, setSuppliers] = useState<Supplier[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [isAssignCustomerOpen, setIsAssignCustomerOpen] = useState(false);
    const [isAssignCustomerSubmitting, setIsAssignCustomerSubmitting] = useState(false);
    const [assignCustomerId, setAssignCustomerId] = useState("");
    const [assignCustomerLabel, setAssignCustomerLabel] = useState("Primary");
    const [assignCustomerIsPrimary, setAssignCustomerIsPrimary] = useState(false);
    const [assignCustomerNotes, setAssignCustomerNotes] = useState("");
    const [isAssignSupplierOpen, setIsAssignSupplierOpen] = useState(false);
    const [isAssignSupplierSubmitting, setIsAssignSupplierSubmitting] = useState(false);
    const [assignSupplierId, setAssignSupplierId] = useState("");
    const [assignSupplierLabel, setAssignSupplierLabel] = useState("Primary");
    const [assignSupplierIsPrimary, setAssignSupplierIsPrimary] = useState(false);
    const [assignSupplierNotes, setAssignSupplierNotes] = useState("");
    const [isEditAddressOpen, setIsEditAddressOpen] = useState(false);
    const [isEditAddressSubmitting, setIsEditAddressSubmitting] = useState(false);
    const [editAddressLine1, setEditAddressLine1] = useState("");
    const [editAddressLine2, setEditAddressLine2] = useState("");
    const [editCity, setEditCity] = useState("");
    const [editState, setEditState] = useState("");
    const [editPostalCode, setEditPostalCode] = useState("");
    const [editCountry, setEditCountry] = useState("US");
    const locationState = location.state as LocationDetailLocationState | null;
    const backTarget = locationState?.fromInvoiceId
        ? `/invoices/${locationState.fromInvoiceId}`
        : locationState?.fromCustomerId
            ? `/customers/${locationState.fromCustomerId}`
            : "/locations";
    const backLabel = locationState?.fromInvoiceId
        ? "Back to invoice"
        : locationState?.fromCustomerId
            ? "Back to customer"
            : "Back to locations";

    async function loadLocationDetail() {
        const parsedLocationId = Number(locationId);

        if (!Number.isInteger(parsedLocationId) || parsedLocationId <= 0) {
            setError("Invalid location id.");
            setIsLoading(false);
            return;
        }

        try {
            setIsLoading(true);
            setError(null);
            const nextDetail = await getLocation(parsedLocationId);
            setDetail({
                ...nextDetail,
                customer_assignments: nextDetail.customer_assignments ?? [],
                supplier_assignments: nextDetail.supplier_assignments ?? [],
                invoices: nextDetail.invoices ?? [],
            });
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to load location detail.");
        } finally {
            setIsLoading(false);
        }
    }

    useEffect(() => {
        loadLocationDetail();
    }, [locationId]);

    function openCustomerDetail(customerId: number) {
        navigate(`/customers/${customerId}`);
    }

    function openInvoiceDetail(invoiceId: number) {
        navigate(`/invoices/${invoiceId}`);
    }

    async function openAssignCustomer() {
        try {
            setError(null);
            setCustomers(await listCustomers());
            setIsAssignCustomerOpen(true);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to load customers.");
        }
    }

    async function openAssignSupplier() {
        try {
            setError(null);
            setSuppliers(await listSuppliers({ activeOnly: true }));
            setIsAssignSupplierOpen(true);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to load suppliers.");
        }
    }

    function openEditAddress() {
        if (!detail) {
            return;
        }

        setError(null);
        setEditAddressLine1(detail.location.address_line1);
        setEditAddressLine2(detail.location.address_line2 ?? "");
        setEditCity(detail.location.city);
        setEditState(detail.location.state);
        setEditPostalCode(detail.location.postal_code);
        setEditCountry(detail.location.country);
        setIsEditAddressOpen(true);
    }

    function resetAssignCustomerForm() {
        setAssignCustomerId("");
        setAssignCustomerLabel("Primary");
        setAssignCustomerIsPrimary(false);
        setAssignCustomerNotes("");
    }

    function resetAssignSupplierForm() {
        setAssignSupplierId("");
        setAssignSupplierLabel("Primary");
        setAssignSupplierIsPrimary(false);
        setAssignSupplierNotes("");
    }

    function closeAssignCustomer() {
        if (isAssignCustomerSubmitting) {
            return;
        }

        resetAssignCustomerForm();
        setIsAssignCustomerOpen(false);
    }

    function closeAssignSupplier() {
        if (isAssignSupplierSubmitting) {
            return;
        }

        resetAssignSupplierForm();
        setIsAssignSupplierOpen(false);
    }

    function closeEditAddress() {
        if (isEditAddressSubmitting) {
            return;
        }

        setIsEditAddressOpen(false);
    }

    const assignedCustomerIds = new Set(
        detail?.customer_assignments.map((assignment) => assignment.customer_id) ?? []
    );
    const availableCustomers = customers.filter((customer) => !assignedCustomerIds.has(customer.id));
    const assignedSupplierIds = new Set(
        detail?.supplier_assignments.map((assignment) => assignment.supplier_id) ?? []
    );
    const availableSuppliers = suppliers.filter((supplier) => !assignedSupplierIds.has(supplier.id));

    const handleAssignCustomer: SubmitEventHandler<HTMLFormElement> = async (event) => {
        event.preventDefault();

        if (!detail) {
            return;
        }

        if (!assignCustomerId) {
            setError("Customer is required.");
            return;
        }

        if (!assignCustomerLabel.trim()) {
            setError("Location label is required.");
            return;
        }

        try {
            setIsAssignCustomerSubmitting(true);
            setError(null);
            await createCustomerLocation(Number(assignCustomerId), {
                label: assignCustomerLabel.trim(),
                address_line1: detail.location.address_line1,
                address_line2: detail.location.address_line2,
                city: detail.location.city,
                state: detail.location.state,
                postal_code: detail.location.postal_code,
                country: detail.location.country,
                is_primary: assignCustomerIsPrimary,
                notes: assignCustomerNotes.trim() || null,
            });
            resetAssignCustomerForm();
            setIsAssignCustomerOpen(false);
            await loadLocationDetail();
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to assign customer.");
        } finally {
            setIsAssignCustomerSubmitting(false);
        }
    };

    const handleAssignSupplier: SubmitEventHandler<HTMLFormElement> = async (event) => {
        event.preventDefault();

        if (!detail) {
            return;
        }

        if (!assignSupplierId) {
            setError("Supplier is required.");
            return;
        }

        if (!assignSupplierLabel.trim()) {
            setError("Location label is required.");
            return;
        }

        try {
            setIsAssignSupplierSubmitting(true);
            setError(null);
            await createSupplierLocation(Number(assignSupplierId), {
                label: assignSupplierLabel.trim(),
                address_line1: detail.location.address_line1,
                address_line2: detail.location.address_line2,
                city: detail.location.city,
                state: detail.location.state,
                postal_code: detail.location.postal_code,
                country: detail.location.country,
                is_primary: assignSupplierIsPrimary,
                notes: assignSupplierNotes.trim() || null,
            });
            resetAssignSupplierForm();
            setIsAssignSupplierOpen(false);
            await loadLocationDetail();
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to assign supplier.");
        } finally {
            setIsAssignSupplierSubmitting(false);
        }
    };

    const handleUpdateAddress: SubmitEventHandler<HTMLFormElement> = async (event) => {
        event.preventDefault();

        if (!detail) {
            return;
        }

        if (!editAddressLine1.trim() || !editCity.trim() || !editState.trim() || !editPostalCode.trim() || !editCountry.trim()) {
            setError("Address, city, state, ZIP code, and country are required.");
            return;
        }

        try {
            setIsEditAddressSubmitting(true);
            setError(null);
            await updateLocation(detail.location.id, {
                address_line1: editAddressLine1.trim(),
                address_line2: editAddressLine2.trim(),
                city: editCity.trim(),
                state: editState.trim(),
                postal_code: editPostalCode.trim(),
                country: editCountry.trim(),
            });
            setIsEditAddressOpen(false);
            await loadLocationDetail();
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to update address.");
        } finally {
            setIsEditAddressSubmitting(false);
        }
    };

    function handleCustomerRowKeyDown(event: KeyboardEvent<HTMLTableRowElement>, customerId: number) {
        if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            openCustomerDetail(customerId);
        }
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
                <h2>Location Detail</h2>
                <p>Review address history, customer assignments, and invoices.</p>
            </div>

            {isLoading ? (
                <p>Loading location...</p>
            ) : error ? (
                <p className="error-message">{error}</p>
            ) : detail ? (
                <section className="detail-stack">
                    <section className="detail-panel">
                        <div className="section-header">
                            <h3>Address</h3>
                            <div className="section-actions">
                                <button className="small-action-button" type="button" onClick={openEditAddress}>
                                    Edit
                                </button>
                            </div>
                        </div>
                        <div className="location-address-lines" aria-label="Location address">
                            <div className="location-address-line">
                                <p>
                                    <span>Address</span>
                                    <strong>{detail.location.address_line1}</strong>
                                </p>
                                <p>
                                    <span>Unit</span>
                                    <strong>{detail.location.address_line2 || "-"}</strong>
                                </p>
                            </div>
                            <div className="location-address-line">
                                <p>
                                    <span>City</span>
                                    <strong>{detail.location.city}</strong>
                                </p>
                                <p>
                                    <span>State</span>
                                    <strong>{detail.location.state}</strong>
                                </p>
                            </div>
                            <div className="location-address-line">
                                <p>
                                    <span>ZIP Code</span>
                                    <strong>{detail.location.postal_code}</strong>
                                </p>
                                <p>
                                    <span>Country</span>
                                    <strong>{detail.location.country}</strong>
                                </p>
                            </div>
                        </div>
                    </section>

                    <section className="detail-panel">
                        <div className="section-header">
                            <h3>Customers</h3>
                            <div className="section-actions">
                                <button className="primary-button" type="button" onClick={openAssignCustomer}>
                                    Assign Customer
                                </button>
                            </div>
                        </div>

                        {detail.customer_assignments.length === 0 ? (
                            <p className="empty-state">No customers assigned to this location.</p>
                        ) : (
                            <div className="table-wrapper detail-table-wrapper">
                                <table className="data-table">
                                    <thead>
                                        <tr>
                                            <th>Customer</th>
                                            <th>Label</th>
                                            <th>Status</th>
                                            <th>Primary</th>
                                            <th>Notes</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {detail.customer_assignments.map((assignment) => (
                                            <tr
                                                key={assignment.id}
                                                className="clickable-row"
                                                tabIndex={0}
                                                aria-label={`View ${assignment.customer_name}`}
                                                onClick={() => openCustomerDetail(assignment.customer_id)}
                                                onKeyDown={(event) => handleCustomerRowKeyDown(event, assignment.customer_id)}
                                            >
                                                <td>
                                                    <div className="product-name-cell">
                                                        <strong>{assignment.customer_name}</strong>
                                                        <span>{assignment.customer_email}</span>
                                                    </div>
                                                </td>
                                                <td>{assignment.label}</td>
                                                <td><span className="status-badge">{assignment.is_active ? "active" : "inactive"}</span></td>
                                                <td>{assignment.is_primary ? "Yes" : "No"}</td>
                                                <td>{assignment.notes ?? "-"}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </section>

                    <section className="detail-panel">
                        <div className="section-header">
                            <h3>Suppliers</h3>
                            <div className="section-actions">
                                <button className="primary-button" type="button" onClick={openAssignSupplier}>
                                    Assign Supplier
                                </button>
                            </div>
                        </div>
                        {detail.supplier_assignments.length === 0 ? (
                            <p className="empty-state">No suppliers assigned to this location.</p>
                        ) : (
                            <div className="table-wrapper detail-table-wrapper">
                                <table className="data-table">
                                    <thead>
                                        <tr>
                                            <th>Supplier</th>
                                            <th>Label</th>
                                            <th>Status</th>
                                            <th>Primary</th>
                                            <th>Notes</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {detail.supplier_assignments.map((assignment) => (
                                            <tr key={assignment.id}>
                                                <td>
                                                    <div className="product-name-cell">
                                                        <strong>{assignment.supplier_name}</strong>
                                                        <span>{assignment.supplier_email ?? assignment.supplier_phone ?? "No contact info"}</span>
                                                    </div>
                                                </td>
                                                <td>{assignment.label}</td>
                                                <td><span className="status-badge">{assignment.is_active ? "active" : "inactive"}</span></td>
                                                <td>{assignment.is_primary ? "Yes" : "No"}</td>
                                                <td>{assignment.notes ?? "-"}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </section>

                    <section className="detail-panel">
                        <div className="section-header">
                            <h3>Invoice History</h3>
                        </div>

                        {detail.invoices.length === 0 ? (
                            <p className="empty-state">No invoices found for this location.</p>
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
                                                <td>${centsToDollars(invoice.total)}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </section>
                </section>
            ) : (
                <p className="empty-state">Location not found.</p>
            )}

            {isEditAddressOpen && detail && (
                <div className="modal-overlay" role="presentation" onMouseDown={closeEditAddress}>
                    <form
                        className="form-card modal-panel"
                        role="dialog"
                        aria-modal="true"
                        aria-labelledby="edit-address-title"
                        onSubmit={handleUpdateAddress}
                        onMouseDown={(event) => event.stopPropagation()}
                    >
                        <div className="modal-header">
                            <h3 id="edit-address-title">Edit Address</h3>
                            <button className="icon-button" type="button" aria-label="Close edit address" onClick={closeEditAddress}>
                                x
                            </button>
                        </div>

                        <div className="form-grid modal-form-grid">
                            <div className="form-field">
                                <label htmlFor="edit-address-line1">Address</label>
                                <input
                                    id="edit-address-line1"
                                    value={editAddressLine1}
                                    onChange={(event) => setEditAddressLine1(event.target.value)}
                                    placeholder="123 Main St"
                                />
                            </div>
                            <div className="form-field">
                                <label htmlFor="edit-address-line2">Address 2</label>
                                <input
                                    id="edit-address-line2"
                                    value={editAddressLine2}
                                    onChange={(event) => setEditAddressLine2(event.target.value)}
                                    placeholder="Suite 200"
                                />
                            </div>
                            <div className="form-field">
                                <label htmlFor="edit-city">City</label>
                                <input
                                    id="edit-city"
                                    value={editCity}
                                    onChange={(event) => setEditCity(event.target.value)}
                                    placeholder="Orlando"
                                />
                            </div>
                            <div className="form-field">
                                <label htmlFor="edit-state">State</label>
                                <input
                                    id="edit-state"
                                    value={editState}
                                    onChange={(event) => setEditState(event.target.value)}
                                    placeholder="FL"
                                />
                            </div>
                            <div className="form-field">
                                <label htmlFor="edit-postal-code">ZIP code</label>
                                <input
                                    id="edit-postal-code"
                                    value={editPostalCode}
                                    onChange={(event) => setEditPostalCode(event.target.value)}
                                    placeholder="32801"
                                />
                            </div>
                            <div className="form-field">
                                <label htmlFor="edit-country">Country</label>
                                <input
                                    id="edit-country"
                                    value={editCountry}
                                    onChange={(event) => setEditCountry(event.target.value)}
                                    placeholder="US"
                                />
                            </div>
                            <div className="modal-actions">
                                <button className="secondary-button" type="button" onClick={closeEditAddress} disabled={isEditAddressSubmitting}>
                                    Cancel
                                </button>
                                <button className="primary-button" type="submit" disabled={isEditAddressSubmitting}>
                                    {isEditAddressSubmitting ? "Saving..." : "Save Address"}
                                </button>
                            </div>
                        </div>
                    </form>
                </div>
            )}

            {isAssignCustomerOpen && detail && (
                <div className="modal-overlay" role="presentation" onMouseDown={closeAssignCustomer}>
                    <form
                        className="form-card modal-panel"
                        role="dialog"
                        aria-modal="true"
                        aria-labelledby="assign-customer-title"
                        onSubmit={handleAssignCustomer}
                        onMouseDown={(event) => event.stopPropagation()}
                    >
                        <div className="modal-header">
                            <h3 id="assign-customer-title">Assign Customer</h3>
                            <button className="icon-button" type="button" aria-label="Close assign customer" onClick={closeAssignCustomer}>
                                x
                            </button>
                        </div>

                        <div className="form-grid modal-form-grid">
                            <div className="form-field">
                                <label htmlFor="assign-customer">Customer</label>
                                <select
                                    id="assign-customer"
                                    value={assignCustomerId}
                                    onChange={(event) => setAssignCustomerId(event.target.value)}
                                >
                                    <option value="">Select a customer</option>
                                    {availableCustomers.map((customer) => (
                                        <option key={customer.id} value={customer.id}>
                                            {customer.name} - {customer.email}
                                        </option>
                                    ))}
                                </select>
                            </div>
                            <div className="form-field">
                                <label htmlFor="assign-customer-label">Label</label>
                                <input
                                    id="assign-customer-label"
                                    value={assignCustomerLabel}
                                    onChange={(event) => setAssignCustomerLabel(event.target.value)}
                                    placeholder="Primary"
                                />
                            </div>
                            <div className="form-field">
                                <label htmlFor="assign-customer-notes">Notes</label>
                                <input
                                    id="assign-customer-notes"
                                    value={assignCustomerNotes}
                                    onChange={(event) => setAssignCustomerNotes(event.target.value)}
                                    placeholder="Access notes"
                                />
                            </div>
                            <label className="inline-toggle">
                                <input
                                    type="checkbox"
                                    checked={assignCustomerIsPrimary}
                                    onChange={(event) => setAssignCustomerIsPrimary(event.target.checked)}
                                />
                                Primary
                            </label>
                            <div className="modal-actions">
                                <button className="secondary-button" type="button" onClick={closeAssignCustomer} disabled={isAssignCustomerSubmitting}>
                                    Cancel
                                </button>
                                <button className="primary-button" type="submit" disabled={isAssignCustomerSubmitting}>
                                    {isAssignCustomerSubmitting ? "Assigning..." : "Assign Customer"}
                                </button>
                            </div>
                        </div>
                    </form>
                </div>
            )}

            {isAssignSupplierOpen && detail && (
                <div className="modal-overlay" role="presentation" onMouseDown={closeAssignSupplier}>
                    <form
                        className="form-card modal-panel"
                        role="dialog"
                        aria-modal="true"
                        aria-labelledby="assign-supplier-title"
                        onSubmit={handleAssignSupplier}
                        onMouseDown={(event) => event.stopPropagation()}
                    >
                        <div className="modal-header">
                            <h3 id="assign-supplier-title">Assign Supplier</h3>
                            <button className="icon-button" type="button" aria-label="Close assign supplier" onClick={closeAssignSupplier}>
                                x
                            </button>
                        </div>

                        <div className="form-grid modal-form-grid">
                            <div className="form-field">
                                <label htmlFor="assign-supplier">Supplier</label>
                                <select
                                    id="assign-supplier"
                                    value={assignSupplierId}
                                    onChange={(event) => setAssignSupplierId(event.target.value)}
                                >
                                    <option value="">Select a supplier</option>
                                    {availableSuppliers.map((supplier) => (
                                        <option key={supplier.id} value={supplier.id}>
                                            {supplier.name}
                                        </option>
                                    ))}
                                </select>
                            </div>
                            <div className="form-field">
                                <label htmlFor="assign-supplier-label">Label</label>
                                <input
                                    id="assign-supplier-label"
                                    value={assignSupplierLabel}
                                    onChange={(event) => setAssignSupplierLabel(event.target.value)}
                                    placeholder="Primary"
                                />
                            </div>
                            <div className="form-field">
                                <label htmlFor="assign-supplier-notes">Notes</label>
                                <input
                                    id="assign-supplier-notes"
                                    value={assignSupplierNotes}
                                    onChange={(event) => setAssignSupplierNotes(event.target.value)}
                                    placeholder="Receiving notes"
                                />
                            </div>
                            <label className="inline-toggle">
                                <input
                                    type="checkbox"
                                    checked={assignSupplierIsPrimary}
                                    onChange={(event) => setAssignSupplierIsPrimary(event.target.checked)}
                                />
                                Primary
                            </label>
                            <div className="modal-actions">
                                <button className="secondary-button" type="button" onClick={closeAssignSupplier} disabled={isAssignSupplierSubmitting}>
                                    Cancel
                                </button>
                                <button className="primary-button" type="submit" disabled={isAssignSupplierSubmitting}>
                                    {isAssignSupplierSubmitting ? "Assigning..." : "Assign Supplier"}
                                </button>
                            </div>
                        </div>
                    </form>
                </div>
            )}
        </>
    );
}
