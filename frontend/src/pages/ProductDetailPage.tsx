import { useEffect, useState, type SubmitEventHandler } from "react";
import { Link, useParams } from "react-router-dom";
import {
    getProduct,
    listProductCategories,
    updateProduct,
    type Product,
    type ProductCategory,
} from "../api/products";
import {
    addSupplierToProduct,
    listProductSuppliers,
    listSuppliers,
    type Supplier,
} from "../api/suppliers";
import { centsToDollars, dollarsToCents } from "../utils/money";

export function ProductDetailPage() {
    const { productId } = useParams();
    const [product, setProduct] = useState<Product | null>(null);
    const [suppliers, setSuppliers] = useState<Supplier[]>([]);
    const [categories, setCategories] = useState<ProductCategory[]>([]);
    const [availableSuppliers, setAvailableSuppliers] = useState<Supplier[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isInfoEditing, setIsInfoEditing] = useState(false);
    const [isInfoSubmitting, setIsInfoSubmitting] = useState(false);
    const [isDescriptionEditing, setIsDescriptionEditing] = useState(false);
    const [isDescriptionSubmitting, setIsDescriptionSubmitting] = useState(false);
    const [isAddSupplierOpen, setIsAddSupplierOpen] = useState(false);
    const [isAddSupplierSubmitting, setIsAddSupplierSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [editName, setEditName] = useState("");
    const [editCategoryId, setEditCategoryId] = useState("");
    const [editCostDollars, setEditCostDollars] = useState("");
    const [editSellDollars, setEditSellDollars] = useState("");
    const [editDescription, setEditDescription] = useState("");
    const [addSupplierId, setAddSupplierId] = useState("");

    const parsedProductId = Number(productId);

    async function loadProductDetail() {
        if (!Number.isInteger(parsedProductId) || parsedProductId <= 0) {
            setError("Invalid product id.");
            setIsLoading(false);
            return;
        }

        try {
            setIsLoading(true);
            setError(null);

            const [productData, supplierData] = await Promise.all([
                getProduct(parsedProductId),
                listProductSuppliers(parsedProductId),
            ]);

            setProduct(productData);
            setSuppliers(supplierData);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to load product detail.");
        } finally {
            setIsLoading(false);
        }
    }

    useEffect(() => {
        loadProductDetail();
    }, [productId]);

    function startEditingInfo() {
        if (!product) {
            return;
        }

        setError(null);
        setEditName(product.name);
        setEditCategoryId(String(product.category_id));
        setEditCostDollars(centsToDollars(product.cost_cents));
        setEditSellDollars(centsToDollars(product.unit_price_cents));
        setIsInfoEditing(true);

        listProductCategories(true)
            .then(setCategories)
            .catch((err) => {
                setError(err instanceof Error ? err.message : "Failed to load product categories.");
            });
    }

    function cancelEditingInfo() {
        if (isInfoSubmitting) {
            return;
        }

        setIsInfoEditing(false);
        setEditName("");
        setEditCategoryId("");
        setEditCostDollars("");
        setEditSellDollars("");
    }

    const handleUpdateInfo: SubmitEventHandler<HTMLFormElement> = async (event) => {
        event.preventDefault();

        if (!product) {
            return;
        }

        const trimmedName = editName.trim();
        if (!trimmedName) {
            setError("Product name is required.");
            return;
        }

        let costCents: number;
        let sellCents: number;
        try {
            costCents = dollarsToCents(editCostDollars);
            sellCents = dollarsToCents(editSellDollars);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Enter valid dollar amounts.");
            return;
        }

        try {
            setIsInfoSubmitting(true);
            setError(null);

            const updatedProduct = await updateProduct(product.id, {
                name: trimmedName,
                category_id: Number(editCategoryId) || product.category_id,
                cost_cents: costCents,
                unit_price_cents: sellCents,
            });

            setProduct(updatedProduct);
            setIsInfoEditing(false);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to update product.");
        } finally {
            setIsInfoSubmitting(false);
        }
    };

    function startEditingDescription() {
        if (!product) {
            return;
        }

        setError(null);
        setEditDescription(product.description ?? "");
        setIsDescriptionEditing(true);
    }

    function cancelEditingDescription() {
        if (isDescriptionSubmitting) {
            return;
        }

        setEditDescription("");
        setIsDescriptionEditing(false);
    }

    const handleUpdateDescription: SubmitEventHandler<HTMLFormElement> = async (event) => {
        event.preventDefault();

        if (!product) {
            return;
        }

        try {
            setIsDescriptionSubmitting(true);
            setError(null);

            const updatedProduct = await updateProduct(product.id, {
                description: editDescription.trim() || null,
            });

            setProduct(updatedProduct);
            setEditDescription("");
            setIsDescriptionEditing(false);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to update description.");
        } finally {
            setIsDescriptionSubmitting(false);
        }
    };

    async function openAddSupplier() {
        if (!product) {
            return;
        }

        try {
            setError(null);
            setAvailableSuppliers(await listSuppliers({ activeOnly: true }));
            setIsAddSupplierOpen(true);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to load suppliers.");
        }
    }

    function closeAddSupplier() {
        if (isAddSupplierSubmitting) {
            return;
        }

        setAddSupplierId("");
        setIsAddSupplierOpen(false);
    }

    const assignedSupplierIds = new Set(suppliers.map((supplier) => supplier.id));
    const supplierOptions = availableSuppliers.filter((supplier) => !assignedSupplierIds.has(supplier.id));

    const handleAddSupplier: SubmitEventHandler<HTMLFormElement> = async (event) => {
        event.preventDefault();

        if (!product || !addSupplierId) {
            return;
        }

        try {
            setIsAddSupplierSubmitting(true);
            setError(null);
            await addSupplierToProduct(product.id, { supplier_id: Number(addSupplierId) });
            setSuppliers(await listProductSuppliers(product.id));
            setAddSupplierId("");
            setIsAddSupplierOpen(false);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to add supplier.");
        } finally {
            setIsAddSupplierSubmitting(false);
        }
    };

    return (
        <>
            <Link className="back-link" to="/products">Back to products</Link>

            <div className="page-header">
                <h2>Product Detail</h2>
                <p>Review catalog pricing, supplier links, and product notes.</p>
            </div>

            {error && <p className="error-message">{error}</p>}

            {isLoading ? (
                <p>Loading product...</p>
            ) : product ? (
                <section className="detail-stack">
                    <section className="detail-panel">
                        <div className="section-header">
                            <h3>{product.name}</h3>
                            {!isInfoEditing && (
                                <button className="small-action-button" type="button" onClick={startEditingInfo}>
                                    Edit
                                </button>
                            )}
                        </div>

                        {isInfoEditing ? (
                            <form className="form-grid" onSubmit={handleUpdateInfo}>
                                <div className="form-field">
                                    <label htmlFor="product-detail-name">Name</label>
                                    <input
                                        id="product-detail-name"
                                        type="text"
                                        value={editName}
                                        onChange={(event) => setEditName(event.target.value)}
                                    />
                                </div>
                                <div className="form-field">
                                    <label htmlFor="product-detail-category">Category</label>
                                    <select
                                        id="product-detail-category"
                                        value={editCategoryId}
                                        onChange={(event) => setEditCategoryId(event.target.value)}
                                    >
                                        {categories.length === 0 ? (
                                            <option value={product.category_id}>{product.category_name}</option>
                                        ) : (
                                            categories.map((category) => (
                                                <option key={category.id} value={category.id}>
                                                    {category.name}
                                                </option>
                                            ))
                                        )}
                                    </select>
                                </div>
                                <div className="form-field">
                                    <label htmlFor="product-detail-cost">Cost</label>
                                    <input
                                        id="product-detail-cost"
                                        type="text"
                                        value={editCostDollars}
                                        onChange={(event) => setEditCostDollars(event.target.value)}
                                    />
                                </div>
                                <div className="form-field">
                                    <label htmlFor="product-detail-sell">Sell</label>
                                    <input
                                        id="product-detail-sell"
                                        type="text"
                                        value={editSellDollars}
                                        onChange={(event) => setEditSellDollars(event.target.value)}
                                    />
                                </div>
                                <div className="modal-actions">
                                    <button className="secondary-button" type="button" onClick={cancelEditingInfo} disabled={isInfoSubmitting}>
                                        Cancel
                                    </button>
                                    <button className="primary-button" type="submit" disabled={isInfoSubmitting}>
                                        {isInfoSubmitting ? "Saving..." : "Save"}
                                    </button>
                                </div>
                            </form>
                        ) : (
                            <dl className="detail-grid">
                                <div>
                                    <dt>Name</dt>
                                    <dd>{product.name}</dd>
                                </div>
                                <div>
                                    <dt>Category</dt>
                                    <dd>{product.category_name}</dd>
                                </div>
                                <div>
                                    <dt>Cost</dt>
                                    <dd>${centsToDollars(product.cost_cents)}</dd>
                                </div>
                                <div>
                                    <dt>Sell</dt>
                                    <dd>${centsToDollars(product.unit_price_cents)}</dd>
                                </div>
                            </dl>
                        )}
                    </section>

                    <section className="detail-panel">
                        <div className="section-header">
                            <div>
                                <h3>Suppliers</h3>
                                <span className="section-count">{suppliers.length} suppliers</span>
                            </div>
                            <div className="section-actions">
                                <button className="primary-button" type="button" onClick={openAddSupplier}>
                                    Add Supplier
                                </button>
                            </div>
                        </div>

                        {suppliers.length === 0 ? (
                            <p className="empty-state">No suppliers assigned.</p>
                        ) : (
                            <div className="supplier-chip-list">
                                {suppliers.map((supplier) => (
                                    <span className="supplier-chip" key={supplier.id}>
                                        {supplier.name}
                                    </span>
                                ))}
                            </div>
                        )}
                    </section>

                    <section className="detail-panel">
                        <div className="section-header">
                            <h3>Description</h3>
                            {!isDescriptionEditing && (
                                <button className="small-action-button" type="button" onClick={startEditingDescription}>
                                    Edit
                                </button>
                            )}
                        </div>

                        {isDescriptionEditing ? (
                            <form className="form-grid" onSubmit={handleUpdateDescription}>
                                <div className="form-field">
                                    <label htmlFor="product-detail-description">Description</label>
                                    <textarea
                                        id="product-detail-description"
                                        value={editDescription}
                                        onChange={(event) => setEditDescription(event.target.value)}
                                    />
                                </div>
                                <div className="modal-actions">
                                    <button
                                        className="secondary-button"
                                        type="button"
                                        onClick={cancelEditingDescription}
                                        disabled={isDescriptionSubmitting}
                                    >
                                        Cancel
                                    </button>
                                    <button className="primary-button" type="submit" disabled={isDescriptionSubmitting}>
                                        {isDescriptionSubmitting ? "Saving..." : "Save"}
                                    </button>
                                </div>
                            </form>
                        ) : (
                            <p>{product.description || "No description provided."}</p>
                        )}
                    </section>
                </section>
            ) : null}

            {isAddSupplierOpen && (
                <div className="modal-overlay" role="presentation" onMouseDown={closeAddSupplier}>
                    <form
                        className="modal-panel detail-panel"
                        onSubmit={handleAddSupplier}
                        role="dialog"
                        aria-modal="true"
                        aria-labelledby="add-product-supplier-title"
                        onMouseDown={(event) => event.stopPropagation()}
                    >
                        <div className="modal-header">
                            <h3 id="add-product-supplier-title">Add Supplier</h3>
                            <button className="icon-button" type="button" aria-label="Close add supplier" onClick={closeAddSupplier}>
                                x
                            </button>
                        </div>

                        <div className="form-field">
                            <label htmlFor="product-detail-supplier">Supplier</label>
                            <select
                                id="product-detail-supplier"
                                value={addSupplierId}
                                onChange={(event) => setAddSupplierId(event.target.value)}
                            >
                                <option value="">Select supplier</option>
                                {supplierOptions.map((supplier) => (
                                    <option key={supplier.id} value={supplier.id}>
                                        {supplier.name}
                                    </option>
                                ))}
                            </select>
                        </div>

                        {supplierOptions.length === 0 && (
                            <p className="empty-state">No available suppliers to add.</p>
                        )}

                        <div className="modal-actions">
                            <button className="secondary-button" type="button" onClick={closeAddSupplier} disabled={isAddSupplierSubmitting}>
                                Cancel
                            </button>
                            <button className="primary-button" type="submit" disabled={isAddSupplierSubmitting || !addSupplierId}>
                                {isAddSupplierSubmitting ? "Adding..." : "Add Supplier"}
                            </button>
                        </div>
                    </form>
                </div>
            )}
        </>
    );
}
