import { useEffect, useState, type ChangeEvent, type FormEvent } from "react";
import {
    getBusinessProfile,
    saveBusinessProfile,
    type BusinessProfile,
    type BusinessProfilePayload,
} from "../api/businessProfile";

type BusinessProfileForm = {
    businessName: string;
    email: string;
    phone: string;
    website: string;
    defaultPaymentTermsDays: string;
    defaultInvoiceFooter: string;
    defaultTaxRate: string;
    addressLine1: string;
    addressLine2: string;
    city: string;
    state: string;
    postalCode: string;
    waysToPay: string[];
};

type SettingsTab = "business" | "invoice";

const paymentMethodOptions = ["Card", "Bank", "PayPal", "Venmo", "Check"];

const emptyProfile: BusinessProfileForm = {
    businessName: "",
    email: "",
    phone: "",
    website: "",
    defaultPaymentTermsDays: "",
    defaultInvoiceFooter: "",
    defaultTaxRate: "",
    addressLine1: "",
    addressLine2: "",
    city: "",
    state: "",
    postalCode: "",
    waysToPay: [],
};

function parseWaysToPay(value: string | null) {
    if (!value) {
        return [];
    }

    const selectedMethods = value
        .split(",")
        .map((method) => method.trim())
        .filter(Boolean);

    return paymentMethodOptions.filter((method) => selectedMethods.includes(method));
}

function toForm(profile: BusinessProfile): BusinessProfileForm {
    return {
        businessName: profile.business_name ?? "",
        email: profile.email ?? "",
        phone: profile.phone ?? "",
        website: profile.website ?? "",
        defaultPaymentTermsDays: profile.default_payment_terms_days?.toString() ?? "",
        defaultInvoiceFooter: profile.default_invoice_footer ?? "",
        defaultTaxRate: profile.default_tax_rate ?? "",
        addressLine1: profile.address_line1 ?? "",
        addressLine2: profile.address_line2 ?? "",
        city: profile.city ?? "",
        state: profile.state ?? "",
        postalCode: profile.postal_code ?? "",
        waysToPay: parseWaysToPay(profile.ways_to_pay),
    };
}

function optionalValue(value: string) {
    return value.trim() || null;
}

function toPayload(profile: BusinessProfileForm): BusinessProfilePayload {
    return {
        business_name: optionalValue(profile.businessName),
        email: optionalValue(profile.email),
        phone: optionalValue(profile.phone),
        website: optionalValue(profile.website),
        address_line1: optionalValue(profile.addressLine1),
        address_line2: optionalValue(profile.addressLine2),
        city: optionalValue(profile.city),
        state: optionalValue(profile.state),
        postal_code: optionalValue(profile.postalCode),
        default_payment_terms_days: profile.defaultPaymentTermsDays === ""
            ? null
            : Number(profile.defaultPaymentTermsDays),
        ways_to_pay: profile.waysToPay.length > 0 ? profile.waysToPay.join(",") : null,
        default_tax_rate: profile.defaultTaxRate === "" || !/\d/.test(profile.defaultTaxRate)
            ? null
            : profile.defaultTaxRate,
        default_invoice_footer: optionalValue(profile.defaultInvoiceFooter),
    };
}

function formatPaymentTerms(days: string) {
    const trimmedDays = days.trim();
    if (!trimmedDays || Number(trimmedDays) === 0) {
        return "Due on receipt";
    }
    return `Net ${trimmedDays}`;
}

function displayValue(value: string, fallback = "—") {
    return value.trim() || fallback;
}

function displayClassName(value: string) {
    return value.trim() ? undefined : "is-empty";
}

function formatAddressValue(profile: BusinessProfileForm) {
    const locality = [profile.city, profile.state, profile.postalCode]
        .map((part) => part.trim())
        .filter(Boolean)
        .join(", ");

    return [profile.addressLine1, profile.addressLine2, locality]
        .map((part) => part.trim())
        .filter(Boolean)
        .join(" · ") || "—";
}

function formatTaxSetting(profile: BusinessProfileForm) {
    if (!profile.defaultTaxRate) {
        return "—";
    }

    return `${profile.defaultTaxRate}%`;
}

function formatTaxInput(value: string) {
    let hasDecimal = false;
    let digitCount = 0;
    let nextValue = "";

    for (const character of value) {
        if (/\d/.test(character)) {
            if (digitCount >= 7) {
                continue;
            }
            digitCount += 1;
            nextValue += character;
        } else if (character === "." && !hasDecimal) {
            hasDecimal = true;
            nextValue += character;
        }
    }

    return nextValue;
}

export function BusinessProfilePage() {
    const [profile, setProfile] = useState<BusinessProfileForm>(emptyProfile);
    const [savedProfile, setSavedProfile] = useState<BusinessProfileForm>(emptyProfile);
    const [activeTab, setActiveTab] = useState<SettingsTab>("business");
    const [isLoading, setIsLoading] = useState(true);
    const [isEditing, setIsEditing] = useState(false);
    const [isSaving, setIsSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [successMessage, setSuccessMessage] = useState<string | null>(null);

    useEffect(() => {
        async function loadProfile() {
            try {
                setError(null);
                const data = await getBusinessProfile();
                const loadedProfile = toForm(data);
                setProfile(loadedProfile);
                setSavedProfile(loadedProfile);
            } catch (err) {
                setError(err instanceof Error ? err.message : "Failed to load business profile.");
            } finally {
                setIsLoading(false);
            }
        }

        loadProfile();
    }, []);

    function handleChange(event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) {
        const { name, value } = event.target;
        setSuccessMessage(null);
        setProfile((currentProfile) => ({
            ...currentProfile,
            [name]: name === "defaultPaymentTermsDays"
                ? value.replace(/\D/g, "")
                : name === "defaultTaxRate"
                ? formatTaxInput(value)
                : value,
        }));
    }

    function handleEdit() {
        setSuccessMessage(null);
        setIsEditing(true);
    }

    function handleCancelEdit() {
        setProfile(savedProfile);
        setError(null);
        setSuccessMessage(null);
        setIsEditing(false);
    }

    function togglePaymentMethod(method: string) {
        setSuccessMessage(null);
        setProfile((currentProfile) => {
            const isSelected = currentProfile.waysToPay.includes(method);
            return {
                ...currentProfile,
                waysToPay: isSelected
                    ? currentProfile.waysToPay.filter((selectedMethod) => selectedMethod !== method)
                    : [...currentProfile.waysToPay, method],
            };
        });
    }

    async function handleSubmit(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();

        try {
            setIsSaving(true);
            setError(null);
            setSuccessMessage(null);
            const data = await saveBusinessProfile(toPayload(profile));
            const savedData = toForm(data);
            setProfile(savedData);
            setSavedProfile(savedData);
            setIsEditing(false);
            setSuccessMessage("Profile saved.");
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to save business profile.");
        } finally {
            setIsSaving(false);
        }
    }

    return (
        <>
            <div className="page-header">
                <h2>Settings</h2>
                <p>Manage business identity and invoice defaults.</p>
            </div>

            {error && <p className="error-message">{error}</p>}
            {successMessage && <p className="success-message">{successMessage}</p>}

            <div className="segmented-tabs settings-tabs" role="tablist" aria-label="Settings sections">
                <button
                    className={activeTab === "business" ? "active" : ""}
                    type="button"
                    role="tab"
                    aria-selected={activeTab === "business"}
                    onClick={() => setActiveTab("business")}
                >
                    Business Settings
                </button>
                <button
                    className={activeTab === "invoice" ? "active" : ""}
                    type="button"
                    role="tab"
                    aria-selected={activeTab === "invoice"}
                    onClick={() => setActiveTab("invoice")}
                >
                    Invoice Settings
                </button>
            </div>

            <section className="business-profile-layout">
                {!isEditing ? (
                <section className="form-card business-profile-form business-profile-read-panel" aria-label="Business profile settings">
                    <div className="business-profile-card-header">
                        <h3>{activeTab === "business" ? "Business Settings" : "Invoice Settings"}</h3>
                        <button className="secondary-button" type="button" onClick={handleEdit} disabled={isLoading}>
                            Edit Settings
                        </button>
                    </div>

                    {isLoading ? (
                        <p>Loading profile...</p>
                    ) : (
                    <div className="business-profile-read-grid">
                        {activeTab === "business" ? (
                        <>
                        <div className="business-profile-read-item business-profile-wide-field">
                            <span>Business Name</span>
                            <strong className={displayClassName(profile.businessName)}>{displayValue(profile.businessName)}</strong>
                        </div>

                        <div className="business-profile-read-item">
                            <span>Email</span>
                            <strong className={displayClassName(profile.email)}>{displayValue(profile.email)}</strong>
                        </div>

                        <div className="business-profile-read-item">
                            <span>Phone</span>
                            <strong className={displayClassName(profile.phone)}>{displayValue(profile.phone)}</strong>
                        </div>

                        <div className="business-profile-read-item business-profile-wide-field">
                            <span>Website</span>
                            <strong className={displayClassName(profile.website)}>{displayValue(profile.website)}</strong>
                        </div>

                        <div className="business-profile-read-item business-profile-wide-field">
                            <span>Address</span>
                            <strong className={formatAddressValue(profile) === "—" ? "is-empty" : undefined}>
                                {formatAddressValue(profile)}
                            </strong>
                        </div>
                        </>
                        ) : (
                        <>

                        <div className="business-profile-read-item">
                            <span>Default Payment Terms</span>
                            <strong>{formatPaymentTerms(profile.defaultPaymentTermsDays)}</strong>
                        </div>

                        <div className="business-profile-read-item business-profile-wide-field">
                            <span>Default Tax Rate</span>
                            <strong className={profile.defaultTaxRate ? undefined : "is-empty"}>
                                {formatTaxSetting(profile)}
                            </strong>
                        </div>

                        <div className="business-profile-read-item business-profile-wide-field">
                            <span>Ways To Pay</span>
                            <strong className={profile.waysToPay.length > 0 ? undefined : "is-empty"}>
                                {profile.waysToPay.join(", ") || "—"}
                            </strong>
                        </div>

                        <div className="business-profile-read-item business-profile-wide-field">
                            <span>Default Invoice Footer</span>
                            <strong className={displayClassName(profile.defaultInvoiceFooter)}>
                                {displayValue(profile.defaultInvoiceFooter)}
                            </strong>
                        </div>
                        </>
                        )}
                    </div>
                    )}
                </section>
                ) : (
                <form className="form-card business-profile-form" aria-label="Business profile form" onSubmit={handleSubmit}>
                    <div className="business-profile-card-header">
                        <h3>{activeTab === "business" ? "Business Settings" : "Invoice Settings"}</h3>
                        <button className="secondary-button" type="button" onClick={handleCancelEdit} disabled={isSaving}>
                            Cancel
                        </button>
                    </div>

                    {isLoading ? (
                        <p>Loading profile...</p>
                    ) : (
                    <div className="form-grid business-profile-grid">
                        {activeTab === "business" ? (
                        <>
                        <div className="form-field business-profile-wide-field">
                            <label htmlFor="businessName">Business Name</label>
                            <input
                                id="businessName"
                                name="businessName"
                                type="text"
                                value={profile.businessName}
                                onChange={handleChange}
                            />
                        </div>

                        <div className="form-field">
                            <label htmlFor="email">Email</label>
                            <input
                                id="email"
                                name="email"
                                type="email"
                                value={profile.email}
                                onChange={handleChange}
                            />
                        </div>

                        <div className="form-field">
                            <label htmlFor="phone">Phone</label>
                            <input
                                id="phone"
                                name="phone"
                                type="tel"
                                value={profile.phone}
                                onChange={handleChange}
                            />
                        </div>

                        <div className="form-field business-profile-wide-field">
                            <label htmlFor="website">Website</label>
                            <input
                                id="website"
                                name="website"
                                type="text"
                                value={profile.website}
                                onChange={handleChange}
                            />
                        </div>

                        <div className="form-field business-profile-wide-field">
                            <label htmlFor="addressLine1">Address Line 1</label>
                            <input
                                id="addressLine1"
                                name="addressLine1"
                                type="text"
                                value={profile.addressLine1}
                                onChange={handleChange}
                            />
                        </div>

                        <div className="form-field business-profile-wide-field">
                            <label htmlFor="addressLine2">Address Line 2</label>
                            <input
                                id="addressLine2"
                                name="addressLine2"
                                type="text"
                                value={profile.addressLine2}
                                onChange={handleChange}
                            />
                        </div>

                        <div className="form-field">
                            <label htmlFor="city">City</label>
                            <input
                                id="city"
                                name="city"
                                type="text"
                                value={profile.city}
                                onChange={handleChange}
                            />
                        </div>

                        <div className="form-field">
                            <label htmlFor="state">State</label>
                            <input
                                id="state"
                                name="state"
                                type="text"
                                value={profile.state}
                                onChange={handleChange}
                            />
                        </div>

                        <div className="form-field">
                            <label htmlFor="postalCode">Postal Code</label>
                            <input
                                id="postalCode"
                                name="postalCode"
                                type="text"
                                value={profile.postalCode}
                                onChange={handleChange}
                            />
                        </div>
                        </>
                        ) : (
                        <>

                        <div className="form-field business-profile-wide-field">
                            <label htmlFor="defaultPaymentTermsDays">Default Payment Terms</label>
                            <input
                                id="defaultPaymentTermsDays"
                                name="defaultPaymentTermsDays"
                                type="text"
                                inputMode="numeric"
                                value={profile.defaultPaymentTermsDays}
                                onChange={handleChange}
                                placeholder="0"
                            />
                        </div>

                        <div className="form-field business-profile-wide-field">
                            <span className="form-field-label">Ways To Pay</span>
                            <div className="payment-method-chip-group" role="group" aria-label="Ways To Pay">
                                {paymentMethodOptions.map((method) => {
                                    const isSelected = profile.waysToPay.includes(method);
                                    return (
                                        <button
                                            key={method}
                                            className={`payment-method-chip${isSelected ? " is-selected" : ""}`}
                                            type="button"
                                            aria-pressed={isSelected}
                                            onClick={() => togglePaymentMethod(method)}
                                        >
                                            <span className="payment-method-chip-check" aria-hidden="true">
                                                {isSelected ? "✓" : ""}
                                            </span>
                                            {method}
                                        </button>
                                    );
                                })}
                            </div>
                        </div>

                        <div className="form-field business-profile-wide-field">
                            <label htmlFor="defaultTaxRate">Default Tax Rate</label>
                            <div className="tax-rate-input">
                                <input
                                    id="defaultTaxRate"
                                    name="defaultTaxRate"
                                    type="text"
                                    inputMode="decimal"
                                    value={profile.defaultTaxRate}
                                    onChange={handleChange}
                                    placeholder="0"
                                />
                                <span>%</span>
                            </div>
                        </div>

                        <div className="form-field business-profile-wide-field">
                            <label htmlFor="defaultInvoiceFooter">Default Invoice Footer</label>
                            <input
                                id="defaultInvoiceFooter"
                                name="defaultInvoiceFooter"
                                type="text"
                                value={profile.defaultInvoiceFooter}
                                onChange={handleChange}
                                placeholder="Thank you for your business."
                            />
                        </div>
                        </>
                        )}
                    </div>
                    )}

                    <button className="primary-button business-profile-save-button" type="submit" disabled={isLoading || isSaving}>
                        {isSaving ? "Saving..." : "Save Settings"}
                    </button>
                </form>
                )}

                <aside className="detail-panel business-profile-preview" aria-label="Invoice sender preview">
                    <span className="detail-label">Invoice Sender</span>
                    <h3>{profile.businessName.trim() || "Business Name"}</h3>
                    <p>{profile.email.trim() || "billing@example.com"}</p>
                    <p>{profile.phone.trim() || "(555) 555-5555"}</p>
                    <p>
                        {profile.addressLine1.trim() || "Address Line 1"}
                        {profile.addressLine2.trim() ? `, ${profile.addressLine2.trim()}` : ""}
                    </p>
                    <p>
                        {[profile.city, profile.state, profile.postalCode]
                            .map((part) => part.trim())
                            .filter(Boolean)
                            .join(", ") || "City, State, Postal Code"}
                    </p>
                    <p>{profile.website.trim() || "website.com"}</p>
                    <div className="business-profile-preview-defaults">
                        <span>Payment Terms</span>
                        <strong>{formatPaymentTerms(profile.defaultPaymentTermsDays)}</strong>
                    </div>
                    <div className="business-profile-preview-defaults">
                        <span>Ways To Pay</span>
                        <strong>{profile.waysToPay.join(", ") || "No payment methods selected"}</strong>
                    </div>
                    <div className="business-profile-preview-defaults">
                        <span>Default Tax Rate</span>
                        <strong>{formatTaxSetting(profile)}</strong>
                    </div>
                    <div className="business-profile-preview-defaults">
                        <span>Invoice Footer</span>
                        <strong>{profile.defaultInvoiceFooter.trim() || "Thank you for your business."}</strong>
                    </div>
                </aside>
            </section>
        </>
    );
}
