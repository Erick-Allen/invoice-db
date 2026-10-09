import { apiRequest } from "./client";

export type DocumentContent = {
    type: "doc";
    content?: unknown[];
    [key: string]: unknown;
};

export type BusinessDocument = {
    id: number;
    workspace_id: number;
    title: string;
    category: string;
    content_json: DocumentContent;
    content_text: string;
    created_at: string;
    updated_at: string;
};

export type BusinessDocumentPayload = {
    title: string;
    category?: string;
    content_json: DocumentContent;
};

export type BusinessDocumentUpdatePayload = Partial<BusinessDocumentPayload>;

export function listDocuments() {
    return apiRequest<BusinessDocument[]>("/documents/");
}

export function createDocument(payload: BusinessDocumentPayload) {
    return apiRequest<BusinessDocument>("/documents/", {
        method: "POST",
        body: JSON.stringify(payload),
    });
}

export function updateDocument(documentId: number, payload: BusinessDocumentUpdatePayload) {
    return apiRequest<BusinessDocument>(`/documents/${documentId}/`, {
        method: "PATCH",
        body: JSON.stringify(payload),
    });
}

export function deleteDocument(documentId: number) {
    return apiRequest<void>(`/documents/${documentId}/`, {
        method: "DELETE",
    });
}
