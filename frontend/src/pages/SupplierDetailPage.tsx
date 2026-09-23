import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import type { Product } from "../api/products";
import {
    getSupplier,
    listSupplierLocations,
    listSupplierProducts,
    type Supplier,
    type SupplierLocation,
} from "../api/suppliers";
import { centsToDollars } from "../utils/money";

function formatLocationAddress(location: SupplierLocation) {
    const unit = location.address_line2 ? `, ${location.address_line2}` : "";
    return `${location.address_line1}${unit}, ${location.city}, ${location.state} ${location.postal_code}`;
}

export function SupplierDetailPage() {
    const { supplierId } = useParams();
    const navigate = useNavigate();
    const [supplier, setSupplier] = useState<Supplier | null>(null);
    const [locations, setLocations] = useState<SupplierLocation[]>([]);
    const [products, setProducts] = useState<Product[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        async function loadSupplierDetail() {
            const parsedSupplierId = Number(supplierId);

            if (!Number.isInteger(parsedSupplierId) || parsedSupplierId <= 0) {
                setError("Invalid supplier id.");
                setIsLoading(false);
                return;
            }

            try {
                setIsLoading(true);
                setError(null);

                const [supplierData, locationData, productData] = await Promise.all([
                    getSupplier(parsedSupplierId),
                    listSupplierLocations(parsedSupplierId),
                    listSupplierProducts(parsedSupplierId),
                ]);

                setSupplier(supplierData);
                setLocations(locationData);
                setProducts(productData);
            } catch (err) {
                setError(err instanceof Error ? err.message : "Failed to load supplier detail.");
            } finally {
                setIsLoading(false);
            }
        }

        loadSupplierDetail();
    }, [supplierId]);

    function openLocationDetail(locationId: number) {
        navigate(`/locations/${locationId}`);
    }

    function openProductDetail(productId: number) {
        navigate(`/products/${productId}`);
    }

    return (
        <>
            <Link className="back-link" to="/suppliers">Back to suppliers</Link>

            <div className="page-header">
                <h2>Supplier Detail</h2>
                <p>Review supplier information, locations, and assigned products.</p>
            </div>

            {error && <p className="error-message">{error}</p>}

            {isLoading ? (
                <p>Loading supplier...</p>
            ) : supplier ? (
                <section className="detail-stack">
                    <section className="detail-panel">
                        <h3>{supplier.name}</h3>
                        <dl className="detail-grid">
                            <div>
                                <dt>Name</dt>
                                <dd>{supplier.name}</dd>
                            </div>
                            <div>
                                <dt>Status</dt>
                                <dd>{supplier.is_active ? "Active" : "Inactive"}</dd>
                            </div>
                            <div>
                                <dt>Phone</dt>
                                <dd>{supplier.phone ?? "-"}</dd>
                            </div>
                            <div>
                                <dt>Email</dt>
                                <dd>{supplier.email ?? "-"}</dd>
                            </div>
                            <div>
                                <dt>Website</dt>
                                <dd>{supplier.website ?? "-"}</dd>
                            </div>
                        </dl>
                    </section>

                    <section className="detail-panel">
                        <div className="section-header">
                            <h3>Locations</h3>
                            <span className="section-count">{locations.length} locations</span>
                        </div>

                        {locations.length === 0 ? (
                            <p className="empty-state">No locations assigned to this supplier.</p>
                        ) : (
                            <div className="table-wrapper detail-table-wrapper">
                                <table className="data-table">
                                    <thead>
                                        <tr>
                                            <th>Label</th>
                                            <th>Address</th>
                                            <th>Status</th>
                                            <th>Primary</th>
                                            <th>Notes</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {locations.map((location) => (
                                            <tr
                                                key={location.id}
                                                className="clickable-row"
                                                tabIndex={0}
                                                aria-label={`View ${location.label}`}
                                                onClick={() => openLocationDetail(location.location_id)}
                                                onKeyDown={(event) => {
                                                    if (event.key === "Enter" || event.key === " ") {
                                                        event.preventDefault();
                                                        openLocationDetail(location.location_id);
                                                    }
                                                }}
                                            >
                                                <td><strong>{location.label}</strong></td>
                                                <td>{formatLocationAddress(location)}</td>
                                                <td><span className="status-badge">{location.is_active ? "active" : "inactive"}</span></td>
                                                <td>{location.is_primary ? "Yes" : "No"}</td>
                                                <td>{location.notes ?? "-"}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </section>

                    <section className="detail-panel">
                        <div className="section-header">
                            <h3>Products</h3>
                            <span className="section-count">{products.length} products</span>
                        </div>

                        {products.length === 0 ? (
                            <p className="empty-state">No products assigned to this supplier.</p>
                        ) : (
                            <div className="table-wrapper detail-table-wrapper">
                                <table className="data-table">
                                    <thead>
                                        <tr>
                                            <th>Name</th>
                                            <th>Category</th>
                                            <th>Cost</th>
                                            <th>Sell</th>
                                            <th>Status</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {products.map((product) => (
                                            <tr
                                                key={product.id}
                                                className="clickable-row"
                                                tabIndex={0}
                                                aria-label={`View ${product.name}`}
                                                onClick={() => openProductDetail(product.id)}
                                                onKeyDown={(event) => {
                                                    if (event.key === "Enter" || event.key === " ") {
                                                        event.preventDefault();
                                                        openProductDetail(product.id);
                                                    }
                                                }}
                                            >
                                                <td><strong>{product.name}</strong></td>
                                                <td>{product.category_name}</td>
                                                <td>${centsToDollars(product.cost_cents)}</td>
                                                <td>${centsToDollars(product.unit_price_cents)}</td>
                                                <td><span className="status-badge">{product.is_active ? "active" : "inactive"}</span></td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </section>
                </section>
            ) : null}
        </>
    );
}
