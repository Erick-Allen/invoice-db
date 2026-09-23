import { useEffect, useState, type KeyboardEvent, type SubmitEventHandler } from "react";
import { useNavigate } from "react-router-dom";
import {
    createCustomer,
    createCustomerLocation,
    listLocations,
    deleteCustomer,
    listCustomers,
    type Customer,
    type Location,
} from "../api/customers";
import { digitsOnly, formatPhoneNumber, isValidCustomerPhone } from "../utils/phone";

function formatLocationAddress(location: Pick<Location, "address_line1" | "address_line2" | "city" | "state" | "postal_code">) {
    const line2 = location.address_line2 ? `, ${location.address_line2}` : "";
    return `${location.address_line1}${line2}, ${location.city}, ${location.state} ${location.postal_code}`;
}

export function CustomersPage() {
    const navigate = useNavigate();
    const [customers, setCustomers] = useState<Customer[]>([]);
    const [existingLocations, setExistingLocations] = useState<Location[]>([]);
    const [name, setName] = useState("");
    const [email, setEmail] = useState("");
    const [phone, setPhone] = useState("");
    const [customerType, setCustomerType] = useState<Customer["customer_type"]>("residential");
    const [companyName, setCompanyName] = useState("");
    const [primaryLocationMode, setPrimaryLocationMode] = useState<"new" | "existing">("existing");
    const [existingPrimaryLocationId, setExistingPrimaryLocationId] = useState("");
    const [locationLabel, setLocationLabel] = useState("Primary");
    const [addressLine1, setAddressLine1] = useState("");
    const [addressLine2, setAddressLine2] = useState("");
    const [city, setCity] = useState("");
    const [state, setState] = useState("");
    const [postalCode, setPostalCode] = useState("");
    const [country, setCountry] = useState("US");
    const [locationNotes, setLocationNotes] = useState("");
    const [isCreateOverlayOpen, setIsCreateOverlayOpen] = useState(false);

    const [isLoading, setIsLoading] = useState(true);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    async function loadCustomers() {
        try {
            setError(null);
            const data = await listCustomers();
            setCustomers(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to load customers.");
        } finally {
            setIsLoading(false);
        }
    }

    async function loadExistingLocations() {
        setExistingLocations(await listLocations());
    }

    function openCustomerDetail(customerId: number) {
        navigate(`/customers/${customerId}`);
    }

    function resetCreateForm() {
        setName("");
        setEmail("");
        setPhone("");
        setCustomerType("residential");
        setCompanyName("");
        setPrimaryLocationMode("existing");
        setExistingPrimaryLocationId("");
        setLocationLabel("Primary");
        setAddressLine1("");
        setAddressLine2("");
        setCity("");
        setState("");
        setPostalCode("");
        setCountry("US");
        setLocationNotes("");
    }

    function openCreateOverlay() {
        setError(null);
        setIsCreateOverlayOpen(true);
        loadExistingLocations().catch((err) => {
            setError(err instanceof Error ? err.message : "Failed to load existing locations.");
        });
    }

    function closeCreateOverlay() {
        if (isSubmitting) {
            return;
        }

        resetCreateForm();
        setIsCreateOverlayOpen(false);
    }

    function handleCustomerRowKeyDown(event: KeyboardEvent<HTMLTableRowElement>, customerId: number) {
        if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            openCustomerDetail(customerId);
        }
    }

    async function handleDeleteCustomer(customerId: number) {
        const confirmed = window.confirm(
            "Are you sure you want to delete this customer?"
        );

        if (!confirmed) {
            return;
        }

        try {
            setError(null)
            await deleteCustomer(customerId);
            await loadCustomers();
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to delete customer.");
        }
    }

    useEffect(() => {
        loadCustomers();
    }, []);

    const handleSubmit: SubmitEventHandler<HTMLFormElement> = async (event) => {
        event.preventDefault();

        const trimmedName = name.trim();
        const trimmedEmail = email.trim();
        const trimmedLocationLabel = locationLabel.trim();
        const trimmedAddressLine1 = addressLine1.trim();
        const trimmedAddressLine2 = addressLine2.trim();
        const trimmedCity = city.trim();
        const trimmedState = state.trim();
        const trimmedPostalCode = postalCode.trim();
        const trimmedCountry = country.trim();
        const trimmedLocationNotes = locationNotes.trim();
        const selectedExistingLocation = existingLocations.find(
            (location) => location.id === Number(existingPrimaryLocationId)
        );
        const hasLocationInput = primaryLocationMode === "existing"
            ? Boolean(selectedExistingLocation)
            : [
                trimmedLocationLabel,
                trimmedAddressLine1,
                trimmedAddressLine2,
                trimmedCity,
                trimmedState,
                trimmedPostalCode,
                trimmedCountry,
                trimmedLocationNotes,
            ].some(Boolean);

        if (!trimmedName) {
            setError("Customer name is required.");
            return;
        }

        if (!trimmedEmail) {
            setError("Customer email is required.");
            return;
        }

        if (!isValidCustomerPhone(phone)) {
            setError("Customer phone must be exactly 10 digits.");
            return;
        }

        if (primaryLocationMode === "existing" && existingPrimaryLocationId && !selectedExistingLocation) {
            setError("Existing location is required.");
            return;
        }

        if (
            hasLocationInput &&
            primaryLocationMode === "new" &&
            (!trimmedAddressLine1 || !trimmedCity || !trimmedState || !trimmedPostalCode)
        ) {
            setError("Primary location needs address, city, state, and ZIP code.");
            return;
        }

        try {
            setIsSubmitting(true);
            setError(null);

            const customer = await createCustomer({
                name: trimmedName,
                email: trimmedEmail,
                phone: phone.trim() || null,
                customer_type: customerType,
                company_name: customerType === "residential" ? null : companyName.trim() || null,
            });

            if (hasLocationInput) {
                const nextLocationLabel = trimmedLocationLabel || "Primary";
                const nextAddressLine1 = primaryLocationMode === "existing" ? selectedExistingLocation?.address_line1 ?? "" : trimmedAddressLine1;
                const nextAddressLine2 = primaryLocationMode === "existing" ? selectedExistingLocation?.address_line2 ?? null : trimmedAddressLine2 || null;
                const nextCity = primaryLocationMode === "existing" ? selectedExistingLocation?.city ?? "" : trimmedCity;
                const nextState = primaryLocationMode === "existing" ? selectedExistingLocation?.state ?? "" : trimmedState;
                const nextPostalCode = primaryLocationMode === "existing" ? selectedExistingLocation?.postal_code ?? "" : trimmedPostalCode;
                const nextCountry = primaryLocationMode === "existing" ? selectedExistingLocation?.country ?? "US" : trimmedCountry || "US";

                try {
                    await createCustomerLocation(customer.id, {
                        label: nextLocationLabel,
                        address_line1: nextAddressLine1,
                        address_line2: nextAddressLine2,
                        city: nextCity,
                        state: nextState,
                        postal_code: nextPostalCode,
                        country: nextCountry,
                        is_primary: true,
                        notes: trimmedLocationNotes || null,
                    });
                } catch (locationError) {
                    setError(
                        locationError instanceof Error
                            ? `Customer was created, but primary location failed: ${locationError.message}`
                            : "Customer was created, but primary location failed."
                    );
                    await loadCustomers();
                    return;
                }
            }

        resetCreateForm();
        setIsCreateOverlayOpen(false);

        await loadCustomers();
        } catch (err) {
            setError(err instanceof Error ? err.message : "Faild to create customer.");
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
    <>
        <div className="page-header">
        <h2>Customers</h2>
        <p>Create customers and view existing customer records.</p>
        </div>

        <section className="invoice-page-stack">
        {error && <p className="error-message">{error}</p>}

        <div className="section-header">
            <h3>Customer List</h3>
            <div className="section-actions">
                <button className="primary-button" type="button" onClick={openCreateOverlay}>
                    Create Customer
                </button>
            </div>
        </div>

        {isCreateOverlayOpen && (
            <div className="modal-overlay" role="presentation" onMouseDown={closeCreateOverlay}>
	                <form
	                    onSubmit={handleSubmit}
	                    noValidate
	                    className="form-card modal-panel"
                    role="dialog"
                    aria-modal="true"
                    aria-labelledby="create-customer-title"
                    onMouseDown={(event) => event.stopPropagation()}
                >
                    <div className="modal-header">
                        <h3 id="create-customer-title">Create Customer</h3>
                        <button className="icon-button" type="button" aria-label="Close create customer" onClick={closeCreateOverlay}>
                            x
                        </button>
                    </div>

                    <div className="form-grid modal-form-grid">
                        <div className="form-field">
                            <label htmlFor="name">Name</label>
                            <input
                                id="name"
                                type="text"
                                value={name}
                                onChange={(event) => setName(event.target.value)}
                                placeholder="Jane Doe"
                            />
                        </div>

                        <div className="form-field">
                            <label htmlFor="email">Email</label>
                            <input
                                id="email"
                                type="email"
                                value={email}
                                onChange={(event) => setEmail(event.target.value)}
                                placeholder="jane@example.com"
                            />
                        </div>

                        <div className="form-field">
                            <label htmlFor="phone">Phone</label>
                            <input
	                                id="phone"
	                                type="text"
	                                inputMode="numeric"
	                                pattern="[0-9]{10}"
	                                maxLength={10}
	                                value={phone}
	                                onChange={(event) => setPhone(digitsOnly(event.target.value).slice(0, 10))}
	                                placeholder="4075550100"
	                            />
                        </div>

                        <div className="form-field">
                            <label htmlFor="customer-type">Type</label>
                            <select
                                id="customer-type"
                                value={customerType}
                                onChange={(event) => {
                                    const nextType = event.target.value as Customer["customer_type"];
                                    setCustomerType(nextType);
                                    if (nextType === "residential") {
                                        setCompanyName("");
                                    }
                                }}
                            >
                                <option value="residential">Residential</option>
                                <option value="commercial">Commercial</option>
                                <option value="property_manager">Property Manager</option>
                                <option value="other">Other</option>
                            </select>
                        </div>

                        {customerType !== "residential" && (
                            <div className="form-field">
                                <label htmlFor="company-name">Company</label>
                                <input
                                    id="company-name"
                                    type="text"
                                    value={companyName}
                                    onChange={(event) => setCompanyName(event.target.value)}
                                    placeholder="ABC Property Group"
                                />
                            </div>
                        )}

                        <div className="form-section-heading">
                            <h4>Primary Location</h4>
                        </div>

                        <div className="form-field">
                            <label htmlFor="location-label">Location Label</label>
                            <input
                                id="location-label"
                                type="text"
                                value={locationLabel}
                                onChange={(event) => setLocationLabel(event.target.value)}
                                placeholder="Primary"
                            />
                        </div>

                        <div className="form-field">
                            <label htmlFor="existing-primary-location">Existing Address</label>
                            <select
                                id="existing-primary-location"
                                value={existingPrimaryLocationId}
                                onChange={(event) => setExistingPrimaryLocationId(event.target.value)}
                                disabled={primaryLocationMode === "new"}
                            >
                                <option value="">Select a location</option>
                                {existingLocations.map((location) => (
                                    <option key={location.id} value={location.id}>
                                        {formatLocationAddress(location)}
                                    </option>
                                ))}
                            </select>
                        </div>

                        <label className="inline-toggle">
                            <input
                                type="checkbox"
                                checked={primaryLocationMode === "new"}
                                onChange={(event) => {
                                    setPrimaryLocationMode(event.target.checked ? "new" : "existing");
                                    setExistingPrimaryLocationId("");
                                }}
                            />
                            New Location
                        </label>

                        {primaryLocationMode === "new" && (
                        <>
                        <div className="form-field">
                            <label htmlFor="address-line1">Address</label>
                            <input
                                id="address-line1"
                                type="text"
                                value={addressLine1}
                                onChange={(event) => setAddressLine1(event.target.value)}
                                placeholder="123 Main St"
                            />
                        </div>

                        <div className="form-field">
                            <label htmlFor="address-line2">Address 2</label>
                            <input
                                id="address-line2"
                                type="text"
                                value={addressLine2}
                                onChange={(event) => setAddressLine2(event.target.value)}
                                placeholder="Suite 200"
                            />
                        </div>

                        <div className="form-field">
                            <label htmlFor="location-city">City</label>
                            <input
                                id="location-city"
                                type="text"
                                value={city}
                                onChange={(event) => setCity(event.target.value)}
                                placeholder="Orlando"
                            />
                        </div>

                        <div className="form-field">
                            <label htmlFor="location-state">State</label>
                            <input
                                id="location-state"
                                type="text"
                                value={state}
                                onChange={(event) => setState(event.target.value)}
                                placeholder="FL"
                            />
                        </div>

                        <div className="form-field">
                            <label htmlFor="postal-code">ZIP Code</label>
                            <input
                                id="postal-code"
                                type="text"
                                value={postalCode}
                                onChange={(event) => setPostalCode(event.target.value)}
                                placeholder="32801"
                            />
                        </div>

                        <div className="form-field">
                            <label htmlFor="location-country">Country</label>
                            <input
                                id="location-country"
                                type="text"
                                value={country}
                                onChange={(event) => setCountry(event.target.value)}
                                placeholder="US"
                            />
                        </div>

                        <div className="form-field">
                            <label htmlFor="location-notes">Location Notes</label>
                            <input
                                id="location-notes"
                                type="text"
                                value={locationNotes}
                                onChange={(event) => setLocationNotes(event.target.value)}
                                placeholder="Gate code, parking, or access notes"
                            />
                        </div>
                        </>
                        )}

                        <div className="modal-actions">
                            <button className="secondary-button" type="button" onClick={closeCreateOverlay} disabled={isSubmitting}>
                                Cancel
                            </button>
                            <button className="primary-button" type="submit" disabled={isSubmitting}>
                                {isSubmitting ? "Creating..." : "Create Customer"}
                            </button>
                        </div>
                    </div>
                </form>
            </div>
        )}

        <div className="table-wrapper wide-table-wrapper">
            {isLoading ? (
            <p>Loading customers...</p>
            ) : customers.length === 0 ? (
            <p>No customers found.</p>
            ) : (
            <table className="data-table">
                <thead>
                <tr>
                    <th>#</th>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Phone</th>
                    <th>Type</th>
                    <th>Actions</th>
                </tr>
                </thead>

                <tbody>
                {customers.map((customer, index) => (
                    <tr
                        key={customer.id}
                        className="clickable-row"
                        tabIndex={0}
                        aria-label={`View ${customer.name}`}
                        onClick={() => openCustomerDetail(customer.id)}
                        onKeyDown={(event) => handleCustomerRowKeyDown(event, customer.id)}
                    >
                    <td>{index + 1}</td>

                        <td>
                            <div className="product-name-cell">
                                <strong>{customer.name}</strong>
                                {customer.company_name && <span>{customer.company_name}</span>}
                            </div>
                        </td>
                        <td>{customer.email}</td>
	                        <td>{formatPhoneNumber(customer.phone)}</td>
                        <td>{customer.customer_type ?? "residential"}</td>
                        <td>
                            <div className="name-actions">
                            <button
                                className="small-danger-button"
                                type="button"
                                onClick={(event) => {
                                    event.stopPropagation();
                                    handleDeleteCustomer(customer.id);
                                }}
                            >
                                Delete
                            </button>
                            </div>
                        </td>
                    </tr>
                ))}
                </tbody>
            </table>
            )}
        </div>
        </section>
    </>
    );
}
