import { useEffect, useState, type SubmitEventHandler } from "react";
import { centsToDollars, dollarsToCents } from "../utils/money";
import {
    createProduct,
    createProductCategory,
    deactivateProduct,
    deactivateProductCategory,
    deleteProduct,
    listProductCategories,
    listProducts,
    updateProduct,
    updateProductCategory,
    type Product,
    type ProductCategory,
} from "../api/products";

export function ProductsPage() {
    const [products, setProducts] = useState<Product[]>([]);
    const [categories, setCategories] = useState<ProductCategory[]>([]);
    const [activeTab, setActiveTab] = useState<"products" | "categories">("products");

    const [name, setName] = useState("");
    const [description, setDescription] = useState("");
    const [unitPriceDollars, setUnitPriceDollars] = useState("");
    const [categoryId, setCategoryId] = useState("1");
    const [categoryFilterId, setCategoryFilterId] = useState("all");
    const [activeOnly, setActiveOnly] = useState(false);
    const [isCreateOverlayOpen, setIsCreateOverlayOpen] = useState(false);

    const [editingProductId, setEditingProductId] = useState<number | null>(null);
    const [editName, setEditName] = useState("");
    const [editDescription, setEditDescription] = useState("");
    const [editUnitPriceDollars, setEditUnitPriceDollars] = useState("");
    const [editCategoryId, setEditCategoryId] = useState("1");
    const [editIsActive, setEditIsActive] = useState(true);

    const [categoryName, setCategoryName] = useState("");
    const [categoryDescription, setCategoryDescription] = useState("");
    const [isCreateCategoryOverlayOpen, setIsCreateCategoryOverlayOpen] = useState(false);
    const [editingCategoryId, setEditingCategoryId] = useState<number | null>(null);
    const [editCategoryName, setEditCategoryName] = useState("");
    const [editCategoryDescription, setEditCategoryDescription] = useState("");
    const [editCategoryIsActive, setEditCategoryIsActive] = useState(true);

    const [isLoading, setIsLoading] = useState(true);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const activeCategories = categories.filter((category) => category.is_active);
    const filteredProducts = categoryFilterId === "all"
        ? products
        : products.filter((product) => product.category_id === Number(categoryFilterId));

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

    async function loadCategories() {
        const data = await listProductCategories();
        setCategories(data);
    }

    async function loadCatalog(nextActiveOnly = activeOnly) {
        try {
            setIsLoading(true);
            setError(null);
            const [productData, categoryData] = await Promise.all([
                listProducts(nextActiveOnly),
                listProductCategories(),
            ]);
            setProducts(productData);
            setCategories(categoryData);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to load product catalog.");
        } finally {
            setIsLoading(false);
        }
    }

    useEffect(() => {
        loadCatalog();
    }, []);

    function resetCreateForm() {
        setName("");
        setDescription("");
        setUnitPriceDollars("");
        setCategoryId("1");
    }

    function openCreateOverlay() {
        setError(null);
        setIsCreateOverlayOpen(true);
    }

    function closeCreateOverlay() {
        if (isSubmitting) {
            return;
        }

        resetCreateForm();
        setIsCreateOverlayOpen(false);
    }

    function startEditingProduct(product: Product) {
        setEditingProductId(product.id);
        setEditName(product.name);
        setEditDescription(product.description ?? "");
        setEditUnitPriceDollars(centsToDollars(product.unit_price_cents));
        setEditCategoryId(String(product.category_id));
        setEditIsActive(product.is_active);
    }

    function cancelEditingProduct() {
        setEditingProductId(null);
        setEditName("");
        setEditDescription("");
        setEditUnitPriceDollars("");
        setEditCategoryId("1");
        setEditIsActive(true);
    }

    function startEditingCategory(category: ProductCategory) {
        setEditingCategoryId(category.id);
        setEditCategoryName(category.name);
        setEditCategoryDescription(category.description ?? "");
        setEditCategoryIsActive(category.is_active);
    }

    function cancelEditingCategory() {
        setEditingCategoryId(null);
        setEditCategoryName("");
        setEditCategoryDescription("");
        setEditCategoryIsActive(true);
    }

    function resetCreateCategoryForm() {
        setCategoryName("");
        setCategoryDescription("");
    }

    function openCreateCategoryOverlay() {
        setError(null);
        setIsCreateCategoryOverlayOpen(true);
    }

    function closeCreateCategoryOverlay() {
        if (isSubmitting) {
            return;
        }

        resetCreateCategoryForm();
        setIsCreateCategoryOverlayOpen(false);
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
                category_id: Number(categoryId) || 1,
                is_active: true,
            });

            resetCreateForm();
            setIsCreateOverlayOpen(false);

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
                category_id: Number(editCategoryId) || 1,
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

    const handleCreateCategory: SubmitEventHandler<HTMLFormElement> = async (event) => {
        event.preventDefault();

        const trimmedName = categoryName.trim();
        if (!trimmedName) {
            setError("Category name is required.");
            return;
        }

        try {
            setIsSubmitting(true);
            setError(null);
            await createProductCategory({
                name: trimmedName,
                description: categoryDescription.trim() || null,
                is_active: true,
            });
            resetCreateCategoryForm();
            setIsCreateCategoryOverlayOpen(false);
            await loadCategories();
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to create category.");
        } finally {
            setIsSubmitting(false);
        }
    };

    async function handleUpdateCategory(categoryIdToUpdate: number) {
        const trimmedName = editCategoryName.trim();
        if (!trimmedName) {
            setError("Category name is required.");
            return;
        }

        try {
            setError(null);
            await updateProductCategory(categoryIdToUpdate, {
                name: trimmedName,
                description: editCategoryDescription.trim() || null,
                is_active: editCategoryIsActive,
            });
            cancelEditingCategory();
            await loadCategories();
            await loadProducts();
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to update category.");
        }
    }

    async function handleDeactivateCategory(categoryIdToDeactivate: number) {
        try {
            setError(null);
            await deactivateProductCategory(categoryIdToDeactivate);
            await loadCategories();
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to deactivate category.");
        }
    }

    return (
        <>
            <div className="page-header">
                <h2>Products</h2>
                <p>Manage reusable catalog items for future invoice workflows.</p>
            </div>

            <section className="invoice-page-stack">
                {error && <p className="error-message">{error}</p>}

                <div className="section-header">
                    <div className="segmented-tabs" role="tablist" aria-label="Product catalog sections">
                        <button
                            type="button"
                            className={activeTab === "products" ? "active" : ""}
                            onClick={() => setActiveTab("products")}
                        >
                            Products
                        </button>
                        <button
                            type="button"
                            className={activeTab === "categories" ? "active" : ""}
                            onClick={() => setActiveTab("categories")}
                        >
                            Categories
                        </button>
                    </div>
                    <div className="section-actions">
                        {activeTab === "products" ? (
                                <button className="primary-button" type="button" onClick={openCreateOverlay}>
                                    Create Product
                                </button>
                            ) : (
                                <button className="primary-button" type="button" onClick={openCreateCategoryOverlay}>
                                    Create Category
                                </button>
                            )}
                    </div>
                </div>

                {isCreateOverlayOpen && (
                    <div className="modal-overlay" role="presentation" onMouseDown={closeCreateOverlay}>
                        <form
                            onSubmit={handleSubmit}
                            className="form-card modal-panel"
                            role="dialog"
                            aria-modal="true"
                            aria-labelledby="create-product-title"
                            onMouseDown={(event) => event.stopPropagation()}
                        >
                            <div className="modal-header">
                                <h3 id="create-product-title">Create Product</h3>
                                <button className="icon-button" type="button" aria-label="Close create product" onClick={closeCreateOverlay}>
                                    x
                                </button>
                            </div>

                            <div className="form-grid modal-form-grid">
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

                                <div className="form-field">
                                    <label htmlFor="product-category">Category</label>
                                    <select
                                        id="product-category"
                                        value={categoryId}
                                        onChange={(event) => setCategoryId(event.target.value)}
                                    >
                                        {activeCategories.length === 0 ? (
                                            <option value="1">Uncategorized</option>
                                        ) : (
                                            activeCategories.map((category) => (
                                                <option key={category.id} value={category.id}>
                                                    {category.name}
                                                </option>
                                            ))
                                        )}
                                    </select>
                                </div>

                                <div className="modal-actions">
                                    <button className="secondary-button" type="button" onClick={closeCreateOverlay} disabled={isSubmitting}>
                                        Cancel
                                    </button>
                                    <button className="primary-button" type="submit" disabled={isSubmitting}>
                                        {isSubmitting ? "Creating..." : "Create Product"}
                                    </button>
                                </div>
                            </div>
                        </form>
                    </div>
                )}

                {activeTab === "products" && (
                    <>
                        <div className="section-header">
                            <h3>Catalog</h3>
                            <div className="section-actions">
                                <label className="compact-filter">
                                    Category
                                    <select
                                        value={categoryFilterId}
                                        onChange={(event) => setCategoryFilterId(event.target.value)}
                                    >
                                        <option value="all">All</option>
                                        {categories.map((category) => (
                                            <option key={category.id} value={category.id}>
                                                {category.name}
                                            </option>
                                        ))}
                                    </select>
                                </label>
                                <label className="inline-toggle">
                                    <input
                                        type="checkbox"
                                        checked={activeOnly}
                                        onChange={(event) => handleActiveOnlyChange(event.target.checked)}
                                    />
                                    Active only
                                </label>
                            </div>
                        </div>

                        <div className="table-wrapper wide-table-wrapper">
                            {isLoading ? (
                                <p>Loading products...</p>
                            ) : filteredProducts.length === 0 ? (
                                <p className="empty-state">No products found.</p>
                            ) : (
                                <table className="data-table">
                                    <thead>
                                        <tr>
                                            <th>#</th>
                                            <th>Name</th>
                                            <th>Category</th>
                                            <th>Description</th>
                                            <th>Unit Price</th>
                                            <th>Status</th>
                                            <th>Actions</th>
                                        </tr>
                                    </thead>

                                    <tbody>
                                        {filteredProducts.map((product, index) => (
                                            <tr key={product.id} className="product-row">
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
                                                            <select
                                                                value={editCategoryId}
                                                                onChange={(event) => setEditCategoryId(event.target.value)}
                                                            >
                                                                {categories.map((category) => (
                                                                    <option key={category.id} value={category.id}>
                                                                        {category.name}
                                                                    </option>
                                                                ))}
                                                            </select>
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
                                                        <td>
                                                            <div className="product-name-cell">
                                                                <strong>{product.name}</strong>
                                                                <span>{product.category_name}</span>
                                                            </div>
                                                        </td>
                                                        <td>{product.category_name}</td>
                                                        <td className="muted-table-cell">{product.description ?? "-"}</td>
                                                        <td className="money-table-cell">${centsToDollars(product.unit_price_cents)}</td>
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
                    </>
                )}

                {activeTab === "categories" && (
                    <section className="invoice-page-stack">
                        {isCreateCategoryOverlayOpen && (
                            <div className="modal-overlay" role="presentation" onMouseDown={closeCreateCategoryOverlay}>
                                <form
                                    className="form-card modal-panel"
                                    onSubmit={handleCreateCategory}
                                    role="dialog"
                                    aria-modal="true"
                                    aria-labelledby="create-category-title"
                                    onMouseDown={(event) => event.stopPropagation()}
                                >
                                    <div className="modal-header">
                                        <h3 id="create-category-title">Create Category</h3>
                                        <button className="icon-button" type="button" aria-label="Close create category" onClick={closeCreateCategoryOverlay}>
                                            x
                                        </button>
                                    </div>

                                    <div className="form-grid modal-form-grid">
                                        <div className="form-field">
                                            <label htmlFor="category-name">Name</label>
                                            <input
                                                id="category-name"
                                                type="text"
                                                value={categoryName}
                                                onChange={(event) => setCategoryName(event.target.value)}
                                                placeholder="Labor"
                                            />
                                        </div>
                                        <div className="form-field">
                                            <label htmlFor="category-description">Description</label>
                                            <input
                                                id="category-description"
                                                type="text"
                                                value={categoryDescription}
                                                onChange={(event) => setCategoryDescription(event.target.value)}
                                                placeholder="Billable work"
                                            />
                                        </div>
                                        <div className="modal-actions">
                                            <button className="secondary-button" type="button" onClick={closeCreateCategoryOverlay} disabled={isSubmitting}>
                                                Cancel
                                            </button>
                                            <button className="primary-button" type="submit" disabled={isSubmitting}>
                                                {isSubmitting ? "Creating..." : "Create Category"}
                                            </button>
                                        </div>
                                    </div>
                                </form>
                            </div>
                        )}

                        <div className="table-wrapper wide-table-wrapper">
                            {isLoading ? (
                                <p>Loading categories...</p>
                            ) : (
                                <table className="data-table">
                                    <thead>
                                        <tr>
                                            <th>Name</th>
                                            <th>Description</th>
                                            <th>Status</th>
                                            <th>Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {categories.map((category) => (
                                            <tr key={category.id}>
                                                {editingCategoryId === category.id ? (
                                                    <>
                                                        <td>
                                                            <input
                                                                type="text"
                                                                value={editCategoryName}
                                                                onChange={(event) => setEditCategoryName(event.target.value)}
                                                            />
                                                        </td>
                                                        <td>
                                                            <input
                                                                className="wide-select"
                                                                type="text"
                                                                value={editCategoryDescription}
                                                                onChange={(event) => setEditCategoryDescription(event.target.value)}
                                                            />
                                                        </td>
                                                        <td>
                                                            <select
                                                                value={editCategoryIsActive ? "active" : "inactive"}
                                                                onChange={(event) => setEditCategoryIsActive(event.target.value === "active")}
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
                                                                    onClick={() => handleUpdateCategory(category.id)}
                                                                >
                                                                    Save
                                                                </button>
                                                                <button
                                                                    className="small-danger-button"
                                                                    type="button"
                                                                    onClick={cancelEditingCategory}
                                                                >
                                                                    Cancel
                                                                </button>
                                                            </div>
                                                        </td>
                                                    </>
                                                ) : (
                                                    <>
                                                        <td><strong>{category.name}</strong></td>
                                                        <td className="muted-table-cell">{category.description ?? "-"}</td>
                                                        <td>
                                                            <span className="status-badge">
                                                                {category.is_active ? "active" : "inactive"}
                                                            </span>
                                                        </td>
                                                        <td>
                                                            <div className="name-actions">
                                                                <button
                                                                    className="small-action-button"
                                                                    type="button"
                                                                    onClick={() => startEditingCategory(category)}
                                                                >
                                                                    Edit
                                                                </button>
                                                                {category.is_active && category.id !== 1 && (
                                                                    <button
                                                                        className="small-action-button"
                                                                        type="button"
                                                                        onClick={() => handleDeactivateCategory(category.id)}
                                                                    >
                                                                        Deactivate
                                                                    </button>
                                                                )}
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
                )}
            </section>
        </>
    );
}
