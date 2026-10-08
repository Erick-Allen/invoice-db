import { apiRequest } from "./client";

export type BusinessProfile = {
    id: number | null;
    workspace_id: number;
    business_name: string | null;
    email: string | null;
    phone: string | null;
    website: string | null;
    address_line1: string | null;
    address_line2: string | null;
    city: string | null;
    state: string | null;
    postal_code: string | null;
    default_payment_terms_days: number | null;
    ways_to_pay: string | null;
    default_tax_rate: string | null;
    default_invoice_footer: string | null;
    logo_url: string | null;
    created_at: string | null;
    updated_at: string | null;
};

export type BusinessProfilePayload = {
    business_name?: string | null;
    email?: string | null;
    phone?: string | null;
    website?: string | null;
    address_line1?: string | null;
    address_line2?: string | null;
    city?: string | null;
    state?: string | null;
    postal_code?: string | null;
    default_payment_terms_days?: number | null;
    ways_to_pay?: string | null;
    default_tax_rate?: string | null;
    default_invoice_footer?: string | null;
    logo_url?: string | null;
};

export function getBusinessProfile() {
    return apiRequest<BusinessProfile>("/business-profile/");
}

export function saveBusinessProfile(payload: BusinessProfilePayload) {
    return apiRequest<BusinessProfile>("/business-profile/", {
        method: "PUT",
        body: JSON.stringify(payload),
    });
}
