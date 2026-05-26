import { apiRequest } from "./client";

export type Customer = {
    id: number;
    name: string;
    email: string;
    created_at?: string;
    updated_at?: string;
};

export type CreateCustomerPayload = {
    name: string;
    email: string;
};

export function listCustomers() {
    return apiRequest<Customer[]>("/customers/");
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