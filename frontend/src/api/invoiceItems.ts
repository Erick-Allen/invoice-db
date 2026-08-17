import { apiRequest } from "./client";

export type InvoiceItem = {
    id: number;
    invoice_id: number;
    product_id: number;
    quantity: number;
    unit_cost_cents: number;
    cost_total_cents: number;
    unit_price_cents: number;
    line_total_cents: number;
};

export type CreateInvoiceItemPayload = {
    product_id: number;
    quantity?: number;
    unit_cost_cents?: number | null;
    unit_price_cents?: number | null;
};

export type UpdateInvoiceItemPayload = {
    product_id?: number;
    quantity?: number;
    unit_cost_cents?: number;
    unit_price_cents?: number;
};

export function createInvoiceItem(invoiceId: number, payload: CreateInvoiceItemPayload) {
    return apiRequest<InvoiceItem>(`/invoices/${invoiceId}/items/`, {
        method: "POST",
        body: JSON.stringify(payload),
    });
}

export function updateInvoiceItem(id: number, payload: UpdateInvoiceItemPayload) {
    return apiRequest<InvoiceItem>(`/invoice-items/${id}/`, {
        method: "PATCH",
        body: JSON.stringify(payload),
    });
}

export function deleteInvoiceItem(id: number) {
    return apiRequest<void>(`/invoice-items/${id}/`, {
        method: "DELETE",
    });
}
