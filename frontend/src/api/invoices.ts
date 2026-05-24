import { apiRequest } from "./client";

export type InvoiceStatus = "draft" | "sent" | "paid" | "void";

export type Invoice = {
    id: number;
    customer_id: number;
    date_issued: string | null;
    date_due: string | null;
    total: number;
    status: InvoiceStatus
};

export type CreateInvoicePayload = {
    customer_id: number;
    date_issued?: string | null;
    date_due?: string | null;
    total: number;
    status?: InvoiceStatus;
};

export function listInvoices() {
    return apiRequest<Invoice[]>("/invoices/");
}

export function createInvoice(payload: CreateInvoicePayload) {
    return apiRequest<Invoice>("/invoices/", {
        method: "POST",
        body: JSON.stringify(payload),
    });
}

export function updateInvoiceStatus(id: number, status: InvoiceStatus) {
    return apiRequest<Invoice>(`/invoices/${id}/status/`, {
        method: "PATCH",
        body: JSON.stringify({ status }),
    });
}