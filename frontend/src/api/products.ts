import { apiRequest } from "./client";

export type Product = {
    id: number;
    name: string;
    description: string | null;
    cost_cents: number;
    unit_price_cents: number;
    category_id: number;
    category_name: string;
    is_active: boolean;
    product_supplier_count?: number;
    invoice_item_count?: number;
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

export type ProductCategoryMetrics = {
    product_count: number;
    active_product_count: number;
    invoice_count: number;
    revenue_total_cents: number;
    cost_total_cents: number;
    profit_total_cents: number;
};

export type ProductCategoryInvoice = {
    id: number;
    customer_id: number;
    customer_name: string;
    date_issued: string | null;
    date_due: string | null;
    status: "draft" | "sent" | "paid" | "void";
    revenue_total_cents: number;
    cost_total_cents: number;
    profit_total_cents: number;
};

export type ProductCategoryDetail = {
    category: ProductCategory;
    metrics: ProductCategoryMetrics;
    products: Product[];
    invoices: ProductCategoryInvoice[];
};

export type CreateProductPayload = {
    name: string;
    description?: string | null;
    cost_cents?: number;
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

export function getProduct(id: number) {
    return apiRequest<Product>(`/products/${id}/`);
}

export function listProductCategories(activeOnly = false) {
    const query = activeOnly ? "?active_only=true" : "";
    return apiRequest<ProductCategory[]>(`/product-categories/${query}`);
}

export function getProductCategoryDetail(id: number) {
    return apiRequest<ProductCategoryDetail>(`/product-categories/${id}/detail/`);
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
