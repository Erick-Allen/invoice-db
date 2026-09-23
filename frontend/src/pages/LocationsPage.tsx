import { useEffect, useState, type FormEvent, type KeyboardEvent } from "react";
import { useNavigate } from "react-router-dom";
import {
    createLocation,
    listLocations,
    type Location,
} from "../api/customers";

function getLocationLinkSummary(location: Location) {
    const hasCustomers = location.assigned_customer_count > 0;
    const hasSuppliers = location.assigned_supplier_count > 0;

    if (hasCustomers && hasSuppliers) {
        return {
            label: `${location.assigned_customer_names ?? "Customer"} | ${location.assigned_supplier_names ?? "Supplier"}`,
            badge: "Both",
            badgeTitle: "Customer and Supplier",
            kind: "both",
        };
    }
    if (hasCustomers) {
        return {
            label: location.assigned_customer_names ?? "Assigned",
            badge: "Customer",
            badgeTitle: "Customer",
            kind: "customer",
        };
    }
    if (hasSuppliers) {
        return {
            label: location.assigned_supplier_names ?? "Assigned",
            badge: "Supplier",
            badgeTitle: "Supplier",
            kind: "supplier",
        };
    }

    return {
        label: "Unassigned",
        badge: null,
        badgeTitle: null,
        kind: "unassigned",
    };
}

function LocationsPanel() {
    const navigate = useNavigate();
    const [locations, setLocations] = useState<Location[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [isCreateOverlayOpen, setIsCreateOverlayOpen] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [addressLine1, setAddressLine1] = useState("");
    const [addressLine2, setAddressLine2] = useState("");
    const [city, setCity] = useState("");
    const [stateInput, setStateInput] = useState("");
    const [postalCode, setPostalCode] = useState("");
    const [country, setCountry] = useState("US");

    async function loadLocations() {
        try {
            setIsLoading(true);
            setError(null);

            setLocations(await listLocations());
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to load locations.");
        } finally {
            setIsLoading(false);
        }
    }

    useEffect(() => {
        loadLocations();
    }, []);

    function openLocationDetail(locationId: number) {
        navigate(`/locations/${locationId}`);
    }

    function handleLocationRowKeyDown(event: KeyboardEvent<HTMLTableRowElement>, locationId: number) {
        if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            openLocationDetail(locationId);
        }
    }

    function resetCreateForm() {
        setAddressLine1("");
        setAddressLine2("");
        setCity("");
        setStateInput("");
        setPostalCode("");
        setCountry("US");
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

    async function handleCreateLocation(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();

        if (!addressLine1.trim() || !city.trim() || !stateInput.trim() || !postalCode.trim()) {
            setError("Address, city, state, and ZIP code are required.");
            return;
        }

        try {
            setIsSubmitting(true);
            setError(null);
            await createLocation({
                address_line1: addressLine1.trim(),
                address_line2: addressLine2.trim() || null,
                city: city.trim(),
                state: stateInput.trim(),
                postal_code: postalCode.trim(),
                country: country.trim() || "US",
            });
            resetCreateForm();
            setIsCreateOverlayOpen(false);
            await loadLocations();
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to create location.");
        } finally {
            setIsSubmitting(false);
        }
    }

    return (
        <section className="invoice-page-stack">
            {error && <p className="error-message">{error}</p>}

            <div className="section-header">
                <h3>Location List</h3>
                <div className="section-actions">
                    <button className="primary-button" type="button" onClick={openCreateOverlay}>
                        Create Location
                    </button>
                </div>
            </div>

            {isCreateOverlayOpen && (
                <div className="modal-overlay" role="presentation" onMouseDown={closeCreateOverlay}>
                    <form
                        className="form-card modal-panel"
                        role="dialog"
                        aria-modal="true"
                        aria-labelledby="create-location-title"
                        onSubmit={handleCreateLocation}
                        onMouseDown={(event) => event.stopPropagation()}
                    >
                        <div className="modal-header">
                            <h3 id="create-location-title">Create Location</h3>
                            <button className="icon-button" type="button" aria-label="Close create location" onClick={closeCreateOverlay}>
                                x
                            </button>
                        </div>

                        <div className="form-grid modal-form-grid">
                            <div className="form-field">
                                <label htmlFor="location-address">Address</label>
                                <input
                                    id="location-address"
                                    type="text"
                                    value={addressLine1}
                                    onChange={(event) => setAddressLine1(event.target.value)}
                                    placeholder="123 Main St"
                                />
                            </div>

                            <div className="form-field">
                                <label htmlFor="location-address-2">Address 2</label>
                                <input
                                    id="location-address-2"
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
                                    value={stateInput}
                                    onChange={(event) => setStateInput(event.target.value)}
                                    placeholder="FL"
                                />
                            </div>

                            <div className="form-field">
                                <label htmlFor="location-postal-code">ZIP Code</label>
                                <input
                                    id="location-postal-code"
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

                            <div className="modal-actions">
                                <button className="secondary-button" type="button" onClick={closeCreateOverlay} disabled={isSubmitting}>
                                    Cancel
                                </button>
                                <button className="primary-button" type="submit" disabled={isSubmitting}>
                                    {isSubmitting ? "Creating..." : "Create Location"}
                                </button>
                            </div>
                        </div>
                    </form>
                </div>
            )}

            <div className="table-wrapper wide-table-wrapper">
                {isLoading ? (
                    <p>Loading locations...</p>
                ) : locations.length === 0 ? (
                    <p>No locations found.</p>
                ) : (
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Address</th>
                                <th>Unit</th>
                                <th>City</th>
                                <th>State</th>
                                <th>ZIP Code</th>
                                <th>Linked To</th>
                            </tr>
                        </thead>
                        <tbody>
                            {locations.map((location) => (
                                <tr
                                    key={location.id}
                                    className="clickable-row"
                                    tabIndex={0}
                                    aria-label={`View location ${location.id}`}
                                    onClick={() => openLocationDetail(location.id)}
                                    onKeyDown={(event) => handleLocationRowKeyDown(event, location.id)}
                                >
                                    <td>
                                        <div className="product-name-cell">
                                            <strong>{location.address_line1}</strong>
                                        </div>
                                    </td>
                                        <td>{location.address_line2 || "-"}</td>
	                                    <td>{location.city}</td>
                                    <td>{location.state}</td>
                                    <td>{location.postal_code}</td>
	                                    <td>
	                                        {(() => {
	                                            const linkSummary = getLocationLinkSummary(location);

	                                            return (
	                                                <div className={`location-link-summary location-link-summary-${linkSummary.kind}`}>
	                                                    <span className="location-link-name">{linkSummary.label}</span>
	                                                    {linkSummary.badge && (
	                                                        <span
	                                                            className={`relationship-badge relationship-badge-${linkSummary.kind}`}
	                                                            title={linkSummary.badgeTitle ?? undefined}
	                                                        >
	                                                            {linkSummary.badge}
	                                                        </span>
	                                                    )}
	                                                </div>
	                                            );
	                                        })()}
	                                    </td>
	                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>
        </section>
    );
}

export function LocationsPage() {
    return (
        <>
            <div className="page-header">
                <h2>Locations</h2>
                <p>Review reusable physical addresses and assign them to customers or suppliers.</p>
            </div>

            <LocationsPanel />
        </>
    );
}
