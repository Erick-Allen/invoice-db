import { fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { getProductCategoryDetail } from "../api/products";
import { CategoryDetailPage } from "../pages/CategoryDetailPage";

vi.mock("../api/products", () => ({
    getProductCategoryDetail: vi.fn(),
}));

const mockedGetProductCategoryDetail = vi.mocked(getProductCategoryDetail);

function LocationDisplay() {
    const location = useLocation();
    return <span data-testid="location-path">{location.pathname}</span>;
}

describe("CategoryDetailPage", () => {
    beforeEach(() => {
        vi.clearAllMocks();

        mockedGetProductCategoryDetail.mockResolvedValue({
            category: {
                id: 2,
                name: "Materials",
                description: "Physical goods",
                is_active: true,
                created_at: "2026-01-01",
                updated_at: "2026-01-01",
            },
            metrics: {
                product_count: 1,
                active_product_count: 1,
                invoice_count: 1,
                revenue_total_cents: 10000,
                cost_total_cents: 4000,
                profit_total_cents: 6000,
            },
            products: [
                {
                    id: 5,
                    name: "Copper Line Set",
                    description: "Line set",
                    cost_cents: 2000,
                    unit_price_cents: 5000,
                    category_id: 2,
                    category_name: "Materials",
                    is_active: true,
                    product_supplier_count: 0,
                    invoice_item_count: 1,
                },
            ],
            invoices: [
                {
                    id: 7,
                    customer_id: 1,
                    customer_name: "John Doe",
                    date_issued: "2026-09-22",
                    date_due: "2026-10-22",
                    status: "sent",
                    revenue_total_cents: 10000,
                    cost_total_cents: 4000,
                    profit_total_cents: 6000,
                },
            ],
        });
    });

    it("renders category info, money metrics, products, and invoice usage", async () => {
        render(
            <MemoryRouter initialEntries={["/categories/2"]}>
                <Routes>
                    <Route path="/categories/:categoryId" element={<CategoryDetailPage />} />
                </Routes>
            </MemoryRouter>
        );

        expect(await screen.findByRole("heading", { name: "Materials" })).toBeInTheDocument();
        expect(mockedGetProductCategoryDetail).toHaveBeenCalledWith(2);
        expect(screen.getByText("Physical goods")).toBeInTheDocument();
        expect(screen.getAllByText("active").length).toBeGreaterThan(0);

        const metrics = screen.getByLabelText("Category money metrics");
        expect(within(metrics).getByText("Products")).toBeInTheDocument();
        expect(within(metrics).getByText("Active Products")).toBeInTheDocument();
        expect(within(metrics).getByText("Invoices")).toBeInTheDocument();
        expect(within(metrics).getByText("$100")).toBeInTheDocument();
        expect(within(metrics).getByText("$40")).toBeInTheDocument();
        expect(within(metrics).getByText("$60")).toBeInTheDocument();

        const productRow = screen.getByRole("row", { name: /View Copper Line Set/i });
        expect(within(productRow).getByText("Copper Line Set")).toBeInTheDocument();
        expect(within(productRow).getByText("$20")).toBeInTheDocument();
        expect(within(productRow).getByText("$50")).toBeInTheDocument();

        const invoiceRow = screen.getByRole("row", { name: /View invoice 7/i });
        expect(within(invoiceRow).getByText("#7")).toBeInTheDocument();
        expect(within(invoiceRow).getByText("John Doe")).toBeInTheDocument();
        expect(within(invoiceRow).getByText("Sep-22-2026")).toBeInTheDocument();
        expect(within(invoiceRow).getByText("sent")).toBeInTheDocument();
    });

    it("opens product detail when a product row is clicked", async () => {
        render(
            <MemoryRouter initialEntries={["/categories/2"]}>
                <Routes>
                    <Route path="/categories/:categoryId" element={<><CategoryDetailPage /><LocationDisplay /></>} />
                    <Route path="/products/:productId" element={<LocationDisplay />} />
                </Routes>
            </MemoryRouter>
        );

        fireEvent.click(await screen.findByRole("row", { name: /View Copper Line Set/i }));

        expect(screen.getByTestId("location-path")).toHaveTextContent("/products/5");
    });

    it("opens invoice detail when an invoice row is clicked", async () => {
        render(
            <MemoryRouter initialEntries={["/categories/2"]}>
                <Routes>
                    <Route path="/categories/:categoryId" element={<><CategoryDetailPage /><LocationDisplay /></>} />
                    <Route path="/invoices/:invoiceId" element={<LocationDisplay />} />
                </Routes>
            </MemoryRouter>
        );

        fireEvent.click(await screen.findByRole("row", { name: /View invoice 7/i }));

        expect(screen.getByTestId("location-path")).toHaveTextContent("/invoices/7");
    });
});
