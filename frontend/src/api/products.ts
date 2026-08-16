import { apiRequest } from "./client";

export type Product = {
    id: number;
    name: string;
    description: string | null;
    unit_price_cents: number;
    category_id: number;
    category_name: string;
    is_active: boolean;
    created_at?: string;
    updated_at?: string;
};

export type ProductCategory = {
    id: number;
    name: string;
    description: string | null;
    is_active: boolean;
    created_at?: string;
    updated_at?: string;
};

export type CreateProductPayload = {
    name: string;
    description?: string | null;
    unit_price_cents: number;
    category_id?: number;
    is_active?: boolean;
};

export type UpdateProductPayload = Partial<CreateProductPayload>;

export type CreateProductCategoryPayload = {
    name: string;
    description?: string | null;
    is_active?: boolean;
};

export type UpdateProductCategoryPayload = Partial<CreateProductCategoryPayload>;

export function listProducts(activeOnly = false) {
    const query = activeOnly ? "?active_only=true" : "";
    return apiRequest<Product[]>(`/products/${query}`);
}

export function listProductCategories(activeOnly = false) {
    const query = activeOnly ? "?active_only=true" : "";
    return apiRequest<ProductCategory[]>(`/product-categories/${query}`);
}

export function createProduct(payload: CreateProductPayload) {
    return apiRequest<Product>("/products/", {
        method: "POST",
        body: JSON.stringify(payload),
    });
}

export function createProductCategory(payload: CreateProductCategoryPayload) {
    return apiRequest<ProductCategory>("/product-categories/", {
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

export function updateProductCategory(id: number, payload: UpdateProductCategoryPayload) {
    return apiRequest<ProductCategory>(`/product-categories/${id}/`, {
        method: "PATCH",
        body: JSON.stringify(payload),
    });
}

export function deactivateProduct(id: number) {
    return apiRequest<Product>(`/products/${id}/deactivate/`, {
        method: "PATCH",
    });
}

export function deactivateProductCategory(id: number) {
    return apiRequest<ProductCategory>(`/product-categories/${id}/deactivate/`, {
        method: "PATCH",
    });
}

export function deleteProductCategory(id: number) {
    return apiRequest<void>(`/product-categories/${id}/`, {
        method: "DELETE",
    });
}

export function deleteProduct(id: number) {
    return apiRequest<void>(`/products/${id}/`, {
        method: "DELETE",
    });
}
