import { apiRequest } from "./client";
import type { Product } from "./products";

export type Supplier = {
    id: number;
    name: string;
    phone: string | null;
    email: string | null;
    website: string | null;
    is_active: boolean;
};

export type ProductSupplier = {
    product_id: number;
    supplier_id: number;
    note: string | null;
    created_at: string;
    updated_at: string;
};

export type CreateSupplierPayload = {
    name: string;
    phone?: string | null;
    email?: string | null;
    website?: string | null;
    is_active?: boolean;
};

export type UpdateSupplierPayload = Partial<CreateSupplierPayload>;

export type CreateProductSupplierPayload = {
    supplier_id: number;
    note?: string | null;
};

export type UpdateProductSupplierPayload = {
    note?: string | null;
};

type ListSupplierOptions = {
    activeOnly?: boolean;
};

export function listSuppliers(options: ListSupplierOptions = {}) {
    const params = new URLSearchParams();

    if (options.activeOnly) {
        params.set("active_only", "true");
    }

    const query = params.toString() ? `?${params.toString()}` : "";
    return apiRequest<Supplier[]>(`/suppliers/${query}`);
}

export function getSupplier(id: number) {
    return apiRequest<Supplier>(`/suppliers/${id}/`);
}

export function createSupplier(payload: CreateSupplierPayload) {
    return apiRequest<Supplier>("/suppliers/", {
        method: "POST",
        body: JSON.stringify(payload),
    });
}

export function updateSupplier(id: number, payload: UpdateSupplierPayload) {
    return apiRequest<Supplier>(`/suppliers/${id}/`, {
        method: "PATCH",
        body: JSON.stringify(payload),
    });
}

export function deactivateSupplier(id: number) {
    return apiRequest<Supplier>(`/suppliers/${id}/deactivate/`, {
        method: "PATCH",
    });
}

export function deleteSupplier(id: number) {
    return apiRequest<void>(`/suppliers/${id}/`, {
        method: "DELETE",
    });
}

export function listSupplierProducts(id: number) {
    return apiRequest<Product[]>(`/suppliers/${id}/products/`);
}

export function removeSupplierFromProducts(id: number) {
    return apiRequest<{ supplier_id: number; removed_count: number }>(
        `/suppliers/${id}/remove-from-products/`,
        {
            method: "POST",
        },
    );
}

export function listProductSuppliers(productId: number) {
    return apiRequest<Supplier[]>(`/products/${productId}/suppliers/`);
}

export function addSupplierToProduct(productId: number, payload: CreateProductSupplierPayload) {
    return apiRequest<ProductSupplier>(`/products/${productId}/suppliers/`, {
        method: "POST",
        body: JSON.stringify(payload),
    });
}

export function updateProductSupplier(productId: number, supplierId: number, payload: UpdateProductSupplierPayload) {
    return apiRequest<ProductSupplier>(`/products/${productId}/suppliers/${supplierId}/`, {
        method: "PATCH",
        body: JSON.stringify(payload),
    });
}

export function removeSupplierFromProduct(productId: number, supplierId: number) {
    return apiRequest<void>(`/products/${productId}/suppliers/${supplierId}/`, {
        method: "DELETE",
    });
}
