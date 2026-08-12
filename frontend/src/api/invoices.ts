import { apiRequest } from "./client";
import type { InvoiceItem } from "./invoiceItems";

export type InvoiceStatus = "draft" | "sent" | "paid" | "void";

export type Invoice = {
    id: number;
    customer_id: number;
    date_issued: string | null;
    date_due: string | null;
    total: number;
    status: InvoiceStatus;
    items?: InvoiceItem[];
};

export type CreateInvoicePayload = {
    customer_id: number;
    date_issued?: string | null;
    date_due?: string | null;
};

export type UpdateInvoicePayload = {
    customer_id?: number;
    date_issued?: string | null;
    date_due?: string | null;
}

type ListInvoiceOptions = {
    includeItems?: boolean;
    customerId?: number;
};

export function listInvoices(options: boolean | ListInvoiceOptions = false) {
    const normalizedOptions = typeof options === "boolean" ? { includeItems: options } : options;
    const params = new URLSearchParams();

    if (normalizedOptions.includeItems) {
        params.set("include_items", "true");
    }

    if (normalizedOptions.customerId !== undefined) {
        params.set("customer_id", String(normalizedOptions.customerId));
    }

    const query = params.toString() ? `?${params.toString()}` : "";
    return apiRequest<Invoice[]>(`/invoices/${query}`);
}

export function getInvoice(id: number, includeItems = false) {
    const query = includeItems ? "?include_items=true" : "";
    return apiRequest<Invoice>(`/invoices/${id}/${query}`);
}

export function createInvoice(payload: CreateInvoicePayload) {
    return apiRequest<Invoice>("/invoices/", {
        method: "POST",
        body: JSON.stringify(payload),
    });
}

export function updateInvoice(id: number, payload: UpdateInvoicePayload) {
    return apiRequest<Invoice>(`/invoices/${id}/`, {
        method: "PATCH",
        body: JSON.stringify(payload)
    });
}


export function updateInvoiceStatus(id: number, status: InvoiceStatus) {
    return apiRequest<Invoice>(`/invoices/${id}/status/`, {
        method: "PATCH",
        body: JSON.stringify({ status }),
    });
}

export function deleteInvoice(id: number) {
    return apiRequest<void>(`/invoices/${id}/`, {
        method: "DELETE",
    })
}
