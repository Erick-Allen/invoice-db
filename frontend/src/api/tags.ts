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
