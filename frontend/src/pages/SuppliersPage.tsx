import { useEffect, useState, type KeyboardEvent, type MouseEvent, type SubmitEventHandler } from "react";
import { useNavigate } from "react-router-dom";
import { listProducts, type Product } from "../api/products";
import {
    createSupplier,
    deactivateSupplier,
    deleteSupplier,
	    listProductSuppliers,
	    listSuppliers,
	    removeSupplierFromProducts,
	    updateSupplier,
	    type Supplier,
} from "../api/suppliers";

export function SuppliersPage() {
    const navigate = useNavigate();
    const [suppliers, setSuppliers] = useState<Supplier[]>([]);
    const [productSuppliers, setProductSuppliers] = useState<Record<number, Supplier[]>>({});
    const [supplierName, setSupplierName] = useState("");
    const [supplierPhone, setSupplierPhone] = useState("");
    const [supplierEmail, setSupplierEmail] = useState("");
    const [supplierWebsite, setSupplierWebsite] = useState("");
    const [isCreateOverlayOpen, setIsCreateOverlayOpen] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const supplierProductCounts = Object.values(productSuppliers)
        .flat()
        .reduce<Record<number, number>>((counts, supplier) => {
            counts[supplier.id] = (counts[supplier.id] ?? 0) + 1;
            return counts;
        }, {});

    async function loadProductSupplierLinks(productData: Product[]) {
        const supplierEntries = await Promise.all(
            productData.map(async (product) => [product.id, await listProductSuppliers(product.id)] as const),
        );

        setProductSuppliers(Object.fromEntries(supplierEntries));
    }

    async function loadSuppliersPage() {
        try {
            setIsLoading(true);
            setError(null);

            const [supplierData, productData] = await Promise.all([
                listSuppliers(),
                listProducts(),
            ]);

            setSuppliers(supplierData);
            await loadProductSupplierLinks(productData);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to load suppliers.");
        } finally {
            setIsLoading(false);
        }
    }

    useEffect(() => {
        loadSuppliersPage();
    }, []);

    function resetCreateSupplierForm() {
        setSupplierName("");
        setSupplierPhone("");
        setSupplierEmail("");
        setSupplierWebsite("");
    }

    function openCreateOverlay() {
        setError(null);
        setIsCreateOverlayOpen(true);
    }

    function closeCreateOverlay() {
        if (isSubmitting) {
            return;
        }

        resetCreateSupplierForm();
        setIsCreateOverlayOpen(false);
    }

    const handleCreateSupplier: SubmitEventHandler<HTMLFormElement> = async (event) => {
        event.preventDefault();

        const trimmedName = supplierName.trim();
        if (!trimmedName) {
            setError("Supplier name is required.");
            return;
        }

        try {
            setIsSubmitting(true);
            setError(null);
            await createSupplier({
                name: trimmedName,
                phone: supplierPhone.trim() || null,
                email: supplierEmail.trim() || null,
                website: supplierWebsite.trim() || null,
                is_active: true,
            });
            resetCreateSupplierForm();
            setIsCreateOverlayOpen(false);
            await loadSuppliersPage();
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to create supplier.");
        } finally {
            setIsSubmitting(false);
        }
    };

	    async function handleDeactivateSupplier(supplierIdToDeactivate: number) {
	        try {
	            setError(null);
	            await deactivateSupplier(supplierIdToDeactivate);
	            await loadSuppliersPage();
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to deactivate supplier.");
	        }
	    }

	    async function handleActivateSupplier(supplierIdToActivate: number) {
	        try {
	            setError(null);
	            await updateSupplier(supplierIdToActivate, { is_active: true });
	            await loadSuppliersPage();
	        } catch (err) {
	            setError(err instanceof Error ? err.message : "Failed to activate supplier.");
	        }
	    }

    async function handleDeleteSupplier(supplierIdToDelete: number) {
        const confirmed = window.confirm("Are you sure you want to delete this supplier?");
        if (!confirmed) {
            return;
        }

        try {
            setError(null);
            await deleteSupplier(supplierIdToDelete);
            await loadSuppliersPage();
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to delete supplier.");
        }
    }

	    async function handleRemoveSupplierFromProducts(supplierIdToRemove: number) {
	        const confirmed = window.confirm("Delete this inactive supplier from every product?");
        if (!confirmed) {
            return;
        }

        try {
            setError(null);
            await removeSupplierFromProducts(supplierIdToRemove);
            await loadSuppliersPage();
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to remove supplier from products.");
        }
    }

    function isInteractiveTarget(target: EventTarget | null) {
        return target instanceof HTMLElement && Boolean(target.closest("button, input, select, textarea, a"));
    }

    function openSupplierDetail(supplierId: number) {
        navigate(`/suppliers/${supplierId}`);
    }

    function handleSupplierRowClick(event: MouseEvent<HTMLTableRowElement>, supplierId: number) {
        if (isInteractiveTarget(event.target)) {
            return;
        }

        openSupplierDetail(supplierId);
    }

    function handleSupplierRowKeyDown(event: KeyboardEvent<HTMLTableRowElement>, supplierId: number) {
        if (isInteractiveTarget(event.target)) {
            return;
        }

        if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            openSupplierDetail(supplierId);
        }
    }

    return (
        <>
            <div className="page-header">
                <h2>Suppliers</h2>
                <p>Manage vendors that source products for invoices.</p>
            </div>

            <section className="invoice-page-stack">
                {error && <p className="error-message">{error}</p>}

                <div className="section-header">
                    <h3>Supplier Directory</h3>
                    <div className="section-actions">
                        <button className="primary-button" type="button" onClick={openCreateOverlay}>
                            Create Supplier
                        </button>
                    </div>
                </div>

                {isCreateOverlayOpen && (
                    <div className="modal-overlay" role="presentation" onMouseDown={closeCreateOverlay}>
                        <form
                            className="form-card modal-panel"
                            onSubmit={handleCreateSupplier}
                            role="dialog"
                            aria-modal="true"
                            aria-labelledby="create-supplier-title"
                            onMouseDown={(event) => event.stopPropagation()}
                        >
                            <div className="modal-header">
                                <h3 id="create-supplier-title">Create Supplier</h3>
                                <button className="icon-button" type="button" aria-label="Close create supplier" onClick={closeCreateOverlay}>
                                    x
                                </button>
                            </div>

                            <div className="form-grid modal-form-grid">
                                <div className="form-field">
                                    <label htmlFor="supplier-name">Name</label>
                                    <input
                                        id="supplier-name"
                                        type="text"
                                        value={supplierName}
                                        onChange={(event) => setSupplierName(event.target.value)}
                                        placeholder="Johnstone Supply"
                                    />
                                </div>
                                <div className="form-field">
                                    <label htmlFor="supplier-phone">Phone</label>
                                    <input
                                        id="supplier-phone"
                                        type="text"
                                        value={supplierPhone}
                                        onChange={(event) => setSupplierPhone(event.target.value)}
                                        placeholder="555-0100"
                                    />
                                </div>
                                <div className="form-field">
                                    <label htmlFor="supplier-email">Email</label>
                                    <input
                                        id="supplier-email"
                                        type="email"
                                        value={supplierEmail}
                                        onChange={(event) => setSupplierEmail(event.target.value)}
                                        placeholder="orders@example.com"
                                    />
                                </div>
                                <div className="form-field">
                                    <label htmlFor="supplier-website">Website</label>
                                    <input
                                        id="supplier-website"
                                        type="url"
                                        value={supplierWebsite}
                                        onChange={(event) => setSupplierWebsite(event.target.value)}
                                        placeholder="https://example.com"
                                    />
                                </div>
                                <div className="modal-actions">
                                    <button className="secondary-button" type="button" onClick={closeCreateOverlay} disabled={isSubmitting}>
                                        Cancel
                                    </button>
                                    <button className="primary-button" type="submit" disabled={isSubmitting}>
                                        {isSubmitting ? "Creating..." : "Create Supplier"}
                                    </button>
                                </div>
                            </div>
                        </form>
                    </div>
                )}

                <div className="table-wrapper wide-table-wrapper">
                    {isLoading ? (
                        <p>Loading suppliers...</p>
                    ) : suppliers.length === 0 ? (
                        <p className="empty-state">No suppliers found.</p>
                    ) : (
                        <table className="data-table">
                            <thead>
                                <tr>
                                    <th>Name</th>
                                    <th>Phone</th>
                                    <th>Email</th>
                                    <th>Website</th>
                                    <th>Status</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {suppliers.map((supplier) => {
                                    const productCount = supplierProductCounts[supplier.id] ?? 0;
                                    const canDeleteSupplier = productCount === 0;
                                    const canDeactivateSupplier = productCount > 0;

                                    return (
                                        <tr
                                            key={supplier.id}
                                            className="clickable-row"
                                            tabIndex={0}
                                            aria-label={`View ${supplier.name}`}
                                            onClick={(event) => handleSupplierRowClick(event, supplier.id)}
                                            onKeyDown={(event) => handleSupplierRowKeyDown(event, supplier.id)}
                                        >
                                            <td><strong>{supplier.name}</strong></td>
                                            <td className="muted-table-cell">{supplier.phone ?? "-"}</td>
                                            <td className="muted-table-cell">{supplier.email ?? "-"}</td>
                                            <td className="muted-table-cell">{supplier.website ?? "-"}</td>
                                            <td>
                                                <span className="status-badge">
                                                    {supplier.is_active ? "active" : "inactive"}
                                                </span>
                                            </td>
                                            <td>
                                                <div className="name-actions">
	                                                    {supplier.is_active && canDeactivateSupplier && (
	                                                        <button
	                                                            className="small-action-button"
                                                            type="button"
                                                            onClick={() => handleDeactivateSupplier(supplier.id)}
                                                        >
	                                                            Deactivate
	                                                        </button>
	                                                    )}
	                                                    {!supplier.is_active && (
	                                                        <button
	                                                            className="small-action-button"
	                                                            type="button"
	                                                            onClick={() => handleActivateSupplier(supplier.id)}
	                                                        >
	                                                            Activate
	                                                        </button>
	                                                    )}
	                                                    {!supplier.is_active && !canDeleteSupplier && (
	                                                        <button
	                                                            className="small-danger-button"
	                                                            type="button"
	                                                            onClick={() => handleRemoveSupplierFromProducts(supplier.id)}
	                                                        >
	                                                            Delete
	                                                        </button>
	                                                    )}
                                                    {canDeleteSupplier && (
                                                        <button
                                                            className="small-danger-button"
                                                            type="button"
                                                            onClick={() => handleDeleteSupplier(supplier.id)}
                                                        >
                                                            Delete
                                                        </button>
                                                    )}
                                                </div>
                                            </td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    )}
                </div>
            </section>
        </>
    );
}
