import { useEffect, useState, type SubmitEventHandler } from "react";
import { centsToDollars, dollarsToCents } from "../utils/money";
import {
    createProduct,
    deactivateProduct,
    deleteProduct,
    listProducts,
    updateProduct,
    type Product,
} from "../api/products";

export function ProductsPage() {
    const [products, setProducts] = useState<Product[]>([]);
    const [name, setName] = useState("");
    const [description, setDescription] = useState("");
    const [unitPriceDollars, setUnitPriceDollars] = useState("");
    const [activeOnly, setActiveOnly] = useState(false);

    const [editingProductId, setEditingProductId] = useState<number | null>(null);
    const [editName, setEditName] = useState("");
    const [editDescription, setEditDescription] = useState("");
    const [editUnitPriceDollars, setEditUnitPriceDollars] = useState("");
    const [editIsActive, setEditIsActive] = useState(true);

    const [isLoading, setIsLoading] = useState(true);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    async function loadProducts(nextActiveOnly = activeOnly) {
        try {
            setError(null);
            const data = await listProducts(nextActiveOnly);
            setProducts(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to load products.");
        } finally {
            setIsLoading(false);
        }
    }

    useEffect(() => {
        loadProducts();
    }, []);

    function startEditingProduct(product: Product) {
        setEditingProductId(product.id);
        setEditName(product.name);
        setEditDescription(product.description ?? "");
        setEditUnitPriceDollars(centsToDollars(product.unit_price_cents));
        setEditIsActive(product.is_active);
    }

    function cancelEditingProduct() {
        setEditingProductId(null);
        setEditName("");
        setEditDescription("");
        setEditUnitPriceDollars("");
        setEditIsActive(true);
    }

    const handleSubmit: SubmitEventHandler<HTMLFormElement> = async (event) => {
        event.preventDefault();

        const trimmedName = name.trim();
        if (!trimmedName) {
            setError("Product name is required.");
            return;
        }

        let unitPriceCents: number;
        try {
            unitPriceCents = dollarsToCents(unitPriceDollars);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Enter a valid product price.");
            return;
        }

        try {
            setIsSubmitting(true);
            setError(null);

            await createProduct({
                name: trimmedName,
                description: description.trim() || null,
                unit_price_cents: unitPriceCents,
                is_active: true,
            });

            setName("");
            setDescription("");
            setUnitPriceDollars("");

            await loadProducts();
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to create product.");
        } finally {
            setIsSubmitting(false);
        }
    };

    async function handleUpdateProduct(productId: number) {
        const trimmedName = editName.trim();
        if (!trimmedName) {
            setError("Product name is required.");
            return;
        }

        let unitPriceCents: number;
        try {
            unitPriceCents = dollarsToCents(editUnitPriceDollars);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Enter a valid product price.");
            return;
        }

        try {
            setError(null);

            await updateProduct(productId, {
                name: trimmedName,
                description: editDescription.trim() || null,
                unit_price_cents: unitPriceCents,
                is_active: editIsActive,
            });

            cancelEditingProduct();
            await loadProducts();
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to update product.");
        }
    }

    async function handleDeactivateProduct(productId: number) {
        try {
            setError(null);
            await deactivateProduct(productId);
            await loadProducts();
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to deactivate product.");
        }
    }

    async function handleDeleteProduct(productId: number) {
        const confirmed = window.confirm("Are you sure you want to delete this product?");
        if (!confirmed) {
            return;
        }

        try {
            setError(null);
            await deleteProduct(productId);
            await loadProducts();
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to delete product.");
        }
    }

    async function handleActiveOnlyChange(checked: boolean) {
        setActiveOnly(checked);
        setIsLoading(true);
        await loadProducts(checked);
    }

    return (
        <>
            <div className="page-header">
                <h2>Products</h2>
                <p>Manage reusable catalog items for future invoice workflows.</p>
            </div>

            <section className="invoice-page-stack">
                {error && <p className="error-message">{error}</p>}

                <form onSubmit={handleSubmit} className="form-card">
                    <div>
                        <h3>Create Product</h3>
                    </div>

                    <div className="form-grid">
                        <div className="form-field">
                            <label htmlFor="product-name">Name</label>
                            <input
                                id="product-name"
                                type="text"
                                value={name}
                                onChange={(event) => setName(event.target.value)}
                                placeholder="Consulting"
                            />
                        </div>

                        <div className="form-field">
                            <label htmlFor="product-description">Description</label>
                            <input
                                id="product-description"
                                type="text"
                                value={description}
                                onChange={(event) => setDescription(event.target.value)}
                                placeholder="Hourly service"
                            />
                        </div>

                        <div className="form-field">
                            <label htmlFor="product-price">Unit Price</label>
                            <input
                                id="product-price"
                                type="text"
                                value={unitPriceDollars}
                                onChange={(event) => setUnitPriceDollars(event.target.value)}
                                placeholder="125.00"
                            />
                        </div>

                        <button className="primary-button" type="submit" disabled={isSubmitting}>
                            {isSubmitting ? "Creating..." : "Create Product"}
                        </button>
                    </div>
                </form>

                <div className="section-header">
                    <h3>Product List</h3>
                    <label className="inline-toggle">
                        <input
                            type="checkbox"
                            checked={activeOnly}
                            onChange={(event) => handleActiveOnlyChange(event.target.checked)}
                        />
                        Active only
                    </label>
                </div>

                <div className="table-wrapper wide-table-wrapper">
                    {isLoading ? (
                        <p>Loading products...</p>
                    ) : products.length === 0 ? (
                        <p className="empty-state">No products found.</p>
                    ) : (
                        <table className="data-table">
                            <thead>
                                <tr>
                                    <th>#</th>
                                    <th>Name</th>
                                    <th>Description</th>
                                    <th>Unit Price</th>
                                    <th>Status</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>

                            <tbody>
                                {products.map((product, index) => (
                                    <tr key={product.id}>
                                        <td>{index + 1}</td>

                                        {editingProductId === product.id ? (
                                            <>
                                                <td>
                                                    <input
                                                        type="text"
                                                        value={editName}
                                                        onChange={(event) => setEditName(event.target.value)}
                                                    />
                                                </td>
                                                <td>
                                                    <input
                                                        className="wide-select"
                                                        type="text"
                                                        value={editDescription}
                                                        onChange={(event) => setEditDescription(event.target.value)}
                                                    />
                                                </td>
                                                <td>
                                                    <input
                                                        type="text"
                                                        value={editUnitPriceDollars}
                                                        onChange={(event) => setEditUnitPriceDollars(event.target.value)}
                                                    />
                                                </td>
                                                <td>
                                                    <select
                                                        value={editIsActive ? "active" : "inactive"}
                                                        onChange={(event) => setEditIsActive(event.target.value === "active")}
                                                    >
                                                        <option value="active">Active</option>
                                                        <option value="inactive">Inactive</option>
                                                    </select>
                                                </td>
                                                <td>
                                                    <div className="name-actions">
                                                        <button
                                                            className="small-action-button"
                                                            type="button"
                                                            onClick={() => handleUpdateProduct(product.id)}
                                                        >
                                                            Save
                                                        </button>
                                                        <button
                                                            className="small-danger-button"
                                                            type="button"
                                                            onClick={cancelEditingProduct}
                                                        >
                                                            Cancel
                                                        </button>
                                                    </div>
                                                </td>
                                            </>
                                        ) : (
                                            <>
                                                <td>{product.name}</td>
                                                <td>{product.description ?? "—"}</td>
                                                <td>${centsToDollars(product.unit_price_cents)}</td>
                                                <td>
                                                    <span className="status-badge">
                                                        {product.is_active ? "active" : "inactive"}
                                                    </span>
                                                </td>
                                                <td>
                                                    <div className="name-actions">
                                                        <button
                                                            className="small-action-button"
                                                            type="button"
                                                            onClick={() => startEditingProduct(product)}
                                                        >
                                                            Edit
                                                        </button>
                                                        {product.is_active && (
                                                            <button
                                                                className="small-action-button"
                                                                type="button"
                                                                onClick={() => handleDeactivateProduct(product.id)}
                                                            >
                                                                Deactivate
                                                            </button>
                                                        )}
                                                        <button
                                                            className="small-danger-button"
                                                            type="button"
                                                            onClick={() => handleDeleteProduct(product.id)}
                                                        >
                                                            Delete
                                                        </button>
                                                    </div>
                                                </td>
                                            </>
                                        )}
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </div>
            </section>
        </>
    );
}
