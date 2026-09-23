import { apiRequest } from "./client";

export type Tag = {
    id: number;
    name: string;
    description: string | null;
    is_active: boolean;
    created_at?: string;
    updated_at?: string;
};

export type InvoiceTag = {
    invoice_id: number;
    tag_id: number;
    created_at: string;
};

export type TagMetrics = {
    invoice_count: number;
    issued_invoice_count: number;
    total_invoiced_cents: number;
    total_cost_cents: number;
    total_paid_cents: number;
    net_profit_cents: number;
    total_owed_cents: number;
};

export type TagInvoice = {
    id: number;
    customer_id: number;
    customer_name: string;
    location_id?: number | null;
    date_issued: string | null;
    date_due: string | null;
    total: number;
    status: "draft" | "sent" | "paid" | "void";
    cost_total_cents: number;
    amount_paid_cents: number;
    balance_due_cents: number;
};

export type TagDetail = {
    tag: Tag;
    metrics: TagMetrics;
    invoices: TagInvoice[];
};

export type CreateTagPayload = {
    name: string;
    description?: string | null;
    is_active?: boolean;
};

export type UpdateTagPayload = Partial<CreateTagPayload>;

export type AddInvoiceTagPayload = {
    tag_id: number;
};

export function listTags(activeOnly = false) {
    const query = activeOnly ? "?active_only=true" : "";
    return apiRequest<Tag[]>(`/tags/${query}`);
}

export function getTag(id: number) {
    return apiRequest<Tag>(`/tags/${id}/`);
}

export function getTagDetail(id: number) {
    return apiRequest<TagDetail>(`/tags/${id}/detail/`);
}

export function createTag(payload: CreateTagPayload) {
    return apiRequest<Tag>("/tags/", {
        method: "POST",
        body: JSON.stringify(payload),
    });
}

export function updateTag(id: number, payload: UpdateTagPayload) {
    return apiRequest<Tag>(`/tags/${id}/`, {
        method: "PATCH",
        body: JSON.stringify(payload),
    });
}

export function deactivateTag(id: number) {
    return apiRequest<Tag>(`/tags/${id}/deactivate/`, {
        method: "PATCH",
    });
}

export function deleteTag(id: number) {
    return apiRequest<void>(`/tags/${id}/`, {
        method: "DELETE",
    });
}

export function listInvoiceTags(invoiceId: number) {
    return apiRequest<Tag[]>(`/invoices/${invoiceId}/tags/`);
}

export function addInvoiceTag(invoiceId: number, payload: AddInvoiceTagPayload) {
    return apiRequest<InvoiceTag>(`/invoices/${invoiceId}/tags/`, {
        method: "POST",
        body: JSON.stringify(payload),
    });
}

export function removeInvoiceTag(invoiceId: number, tagId: number) {
    return apiRequest<void>(`/invoices/${invoiceId}/tags/${tagId}/`, {
        method: "DELETE",
    });
}
