import { apiRequest } from "./client";

export type Customer = {
    id: number;
    name: string;
    email: string;
    phone?: string | null;
    customer_type?: "residential" | "commercial" | "property_manager" | "other";
    company_name?: string | null;
    is_active?: boolean;
    created_at?: string;
    updated_at?: string;
};

export type CustomerLocation = {
    id: number;
    customer_id: number;
    location_id: number;
    label: string;
    address_line1: string;
    address_line2: string | null;
    city: string;
    state: string;
    postal_code: string;
    country: string;
    is_primary: boolean;
    is_active: boolean;
    notes: string | null;
    created_at: string;
    updated_at: string;
};

export type Location = {
    id: number;
    address_line1: string;
    address_line2: string | null;
    city: string;
    state: string;
    postal_code: string;
    country: string;
    assigned_customer_count: number;
    assigned_customer_names: string | null;
    assigned_supplier_count: number;
    assigned_supplier_names: string | null;
    assigned_count: number;
    assigned_names: string | null;
    created_at: string;
    updated_at: string;
};

export type LocationCustomerAssignment = {
    id: number;
    customer_id: number;
    customer_name: string;
    customer_email: string;
    label: string;
    is_primary: boolean;
    is_active: boolean;
    notes: string | null;
    created_at: string;
    updated_at: string;
};

export type LocationSupplierAssignment = {
    id: number;
    supplier_id: number;
    supplier_name: string;
    supplier_phone: string | null;
    supplier_email: string | null;
    label: string;
    is_primary: boolean;
    is_active: boolean;
    notes: string | null;
    created_at: string;
    updated_at: string;
};

export type LocationInvoice = {
    id: number;
    customer_id: number;
    customer_name: string;
    customer_location_id: number;
    date_issued: string | null;
    date_due: string | null;
    total: number;
    status: "draft" | "sent" | "paid" | "void";
};

export type LocationDetail = {
    location: Location;
    customer_assignments: LocationCustomerAssignment[];
    supplier_assignments: LocationSupplierAssignment[];
    invoices: LocationInvoice[];
};

export type CreateCustomerPayload = {
    name: string;
    email: string;
    phone?: string | null;
    customer_type?: Customer["customer_type"];
    company_name?: string | null;
    is_active?: boolean;
};

export type CreateCustomerLocationPayload = {
    label: string;
    address_line1: string;
    address_line2?: string | null;
    city: string;
    state: string;
    postal_code: string;
    country?: string;
    is_primary?: boolean;
    is_active?: boolean;
    notes?: string | null;
};

export type CreateLocationPayload = {
    address_line1: string;
    address_line2?: string | null;
    city: string;
    state: string;
    postal_code: string;
    country?: string;
};

export type UpdateLocationPayload = Partial<CreateLocationPayload>;

export type UpdateCustomerLocationPayload = Partial<CreateCustomerLocationPayload>;

export function listCustomers() {
    return apiRequest<Customer[]>("/customers/");
}

export function getCustomer(id: number) {
    return apiRequest<Customer>(`/customers/${id}/`);
}

export function createCustomer(payload: CreateCustomerPayload) {
    return apiRequest<Customer>("/customers/", {
        method: "POST",
        body: JSON.stringify(payload),
    });
}

export function updateCustomer(id: number, payload: Partial<CreateCustomerPayload>) {
    return apiRequest<Customer>(`/customers/${id}/`, {
        method: "PATCH",
        body: JSON.stringify(payload),
    });
}

export function deleteCustomer(id: number) {
    return apiRequest<void>(`/customers/${id}/`, {
        method: "DELETE",
    });
}

export function listCustomerLocations(customerId: number, activeOnly = false) {
    const query = activeOnly ? "?active_only=true" : "";
    return apiRequest<CustomerLocation[]>(`/customers/${customerId}/locations/${query}`);
}

export function listLocations() {
    return apiRequest<Location[]>("/locations/");
}

export function createLocation(payload: CreateLocationPayload) {
    return apiRequest<Location>("/locations/", {
        method: "POST",
        body: JSON.stringify(payload),
    });
}

export function getLocation(id: number) {
    return apiRequest<LocationDetail>(`/locations/${id}/`);
}

export function updateLocation(id: number, payload: UpdateLocationPayload) {
    return apiRequest<Location>(`/locations/${id}/`, {
        method: "PATCH",
        body: JSON.stringify(payload),
    });
}

export function createCustomerLocation(customerId: number, payload: CreateCustomerLocationPayload) {
    return apiRequest<CustomerLocation>(`/customers/${customerId}/locations/`, {
        method: "POST",
        body: JSON.stringify(payload),
    });
}

export function updateCustomerLocation(customerId: number, locationId: number, payload: UpdateCustomerLocationPayload) {
    return apiRequest<CustomerLocation>(`/customers/${customerId}/locations/${locationId}/`, {
        method: "PATCH",
        body: JSON.stringify(payload),
    });
}

export function deleteCustomerLocation(customerId: number, locationId: number) {
    return apiRequest<void>(`/customers/${customerId}/locations/${locationId}/`, {
        method: "DELETE",
    });
}
