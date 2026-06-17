import { apiRequest } from "./client";

export type Product = {
    id: number;
    name: string;
    description: string | null;
    unit_price_cents: number;
    is_active: boolean;
    created_at?: string;
    updated_at?: string;
};

export type CreateProductPayload = {
    name: string;
    description?: string | null;
    unit_price_cents: number;
    is_active?: boolean;
};

export type UpdateProductPayload = Partial<CreateProductPayload>;

export function listProducts(activeOnly = false) {
    const query = activeOnly ? "?active_only=true" : "";
    return apiRequest<Product[]>(`/products/${query}`);
}

export function createProduct(payload: CreateProductPayload) {
    return apiRequest<Product>("/products/", {
        method: "POST",
        body: JSON.stringify(payload),
    });
}

export function updateProduct(id: number, payload: UpdateProductPayload) {
    return apiRequest<Product>(`/products/${id}/`, {
        method: "PATCH",
        body: JSON.stringify(payload),
    });
}

export function deactivateProduct(id: number) {
    return apiRequest<Product>(`/products/${id}/deactivate/`, {
        method: "PATCH",
    });
}

export function deleteProduct(id: number) {
    return apiRequest<void>(`/products/${id}/`, {
        method: "DELETE",
    });
}
