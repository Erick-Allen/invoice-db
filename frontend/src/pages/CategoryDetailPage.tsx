import { useEffect, useState, type KeyboardEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { getProductCategoryDetail, type ProductCategoryDetail } from "../api/products";
import { formatDisplayDate } from "../utils/date";
import { centsToDollars } from "../utils/money";

function formatCurrency(cents: number) {
    return cents < 0 ? `-$${centsToDollars(Math.abs(cents))}` : `$${centsToDollars(cents)}`;
}

export function CategoryDetailPage() {
    const { categoryId } = useParams();
    const navigate = useNavigate();
    const [detail, setDetail] = useState<ProductCategoryDetail | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        async function loadCategoryDetail() {
            const parsedCategoryId = Number(categoryId);

            if (!Number.isInteger(parsedCategoryId) || parsedCategoryId <= 0) {
                setError("Invalid category id.");
                setIsLoading(false);
                return;
            }

            try {
                setIsLoading(true);
                setError(null);
                setDetail(await getProductCategoryDetail(parsedCategoryId));
            } catch (err) {
                setError(err instanceof Error ? err.message : "Failed to load category detail.");
            } finally {
                setIsLoading(false);
            }
        }

        loadCategoryDetail();
    }, [categoryId]);

    function openProductDetail(productId: number) {
        navigate(`/products/${productId}`);
    }

    function openInvoiceDetail(invoiceId: number) {
        navigate(`/invoices/${invoiceId}`);
    }

    function handleProductRowKeyDown(event: KeyboardEvent<HTMLTableRowElement>, productId: number) {
        if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            openProductDetail(productId);
        }
    }

    function handleInvoiceRowKeyDown(event: KeyboardEvent<HTMLTableRowElement>, invoiceId: number) {
        if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            openInvoiceDetail(invoiceId);
        }
    }

    return (
        <>
            <div className="page-header">
                <Link className="back-link" to="/products">
                    Back to products
                </Link>
                <h2>Category Detail</h2>
                <p>Review category performance, products, and invoice usage.</p>
            </div>

            {isLoading ? (
                <p>Loading category...</p>
            ) : error ? (
                <p className="error-message">{error}</p>
            ) : detail ? (
                <section className="detail-stack">
                    <section className="detail-panel">
                        <div>
                            <span className="detail-label">Category</span>
                            <h3>{detail.category.name}</h3>
                        </div>
                        <dl className="detail-grid">
                            <div>
                                <dt>Status</dt>
                                <dd><span className="status-badge">{detail.category.is_active ? "active" : "inactive"}</span></dd>
                            </div>
                            <div>
                                <dt>Description</dt>
                                <dd>{detail.category.description || "-"}</dd>
                            </div>
                            <div>
                                <dt>Category ID</dt>
                                <dd>{detail.category.id}</dd>
                            </div>
                        </dl>
                    </section>

                    <section className="detail-summary-grid" aria-label="Category money metrics">
                        <div>
                            <span>Products</span>
                            <strong>{detail.metrics.product_count}</strong>
                        </div>
                        <div>
                            <span>Active Products</span>
                            <strong>{detail.metrics.active_product_count}</strong>
                        </div>
                        <div>
                            <span>Invoices</span>
                            <strong>{detail.metrics.invoice_count}</strong>
                        </div>
                        <div>
                            <span>Total Revenue</span>
                            <strong>{formatCurrency(detail.metrics.revenue_total_cents)}</strong>
                        </div>
                        <div>
                            <span>Total Cost</span>
                            <strong>{formatCurrency(detail.metrics.cost_total_cents)}</strong>
                        </div>
                        <div>
                            <span>Gross Profit</span>
                            <strong>{formatCurrency(detail.metrics.profit_total_cents)}</strong>
                        </div>
                    </section>

                    <section className="detail-panel">
                        <div className="section-header">
                            <h3>Products</h3>
                        </div>

                        {detail.products.length === 0 ? (
                            <p className="empty-state">No products are assigned to this category.</p>
                        ) : (
                            <div className="table-wrapper detail-table-wrapper">
                                <table className="data-table">
                                    <thead>
                                        <tr>
                                            <th>Product</th>
                                            <th>Description</th>
                                            <th>Cost</th>
                                            <th>Sell Price</th>
                                            <th>Status</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {detail.products.map((product) => (
                                            <tr
                                                key={product.id}
                                                className="clickable-row"
                                                tabIndex={0}
                                                aria-label={`View ${product.name}`}
                                                onClick={() => openProductDetail(product.id)}
                                                onKeyDown={(event) => handleProductRowKeyDown(event, product.id)}
                                            >
                                                <td><strong>{product.name}</strong></td>
                                                <td className="muted-table-cell">{product.description ?? "-"}</td>
                                                <td>{formatCurrency(product.cost_cents)}</td>
                                                <td>{formatCurrency(product.unit_price_cents)}</td>
                                                <td><span className="status-badge">{product.is_active ? "active" : "inactive"}</span></td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </section>

                    <section className="detail-panel">
                        <div className="section-header">
                            <h3>Invoice Usage</h3>
                        </div>

                        {detail.invoices.length === 0 ? (
                            <p className="empty-state">No invoices have used products from this category.</p>
                        ) : (
                            <div className="table-wrapper detail-table-wrapper">
                                <table className="data-table">
                                    <thead>
                                        <tr>
                                            <th>Invoice</th>
                                            <th>Customer</th>
                                            <th>Issued</th>
                                            <th>Due</th>
                                            <th>Status</th>
                                            <th>Revenue</th>
                                            <th>Cost</th>
                                            <th>Profit</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {detail.invoices.map((invoice) => (
                                            <tr
                                                key={invoice.id}
                                                className="clickable-row"
                                                tabIndex={0}
                                                aria-label={`View invoice ${invoice.id}`}
                                                onClick={() => openInvoiceDetail(invoice.id)}
                                                onKeyDown={(event) => handleInvoiceRowKeyDown(event, invoice.id)}
                                            >
                                                <td>#{invoice.id}</td>
                                                <td>{invoice.customer_name}</td>
                                                <td>{formatDisplayDate(invoice.date_issued)}</td>
                                                <td>{formatDisplayDate(invoice.date_due)}</td>
                                                <td><span className="status-badge">{invoice.status}</span></td>
                                                <td>{formatCurrency(invoice.revenue_total_cents)}</td>
                                                <td>{formatCurrency(invoice.cost_total_cents)}</td>
                                                <td>{formatCurrency(invoice.profit_total_cents)}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </section>
                </section>
            ) : (
                <p className="empty-state">Category not found.</p>
            )}
        </>
    );
}
