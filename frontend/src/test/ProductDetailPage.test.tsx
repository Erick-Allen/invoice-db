import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { getProduct, listProductCategories, updateProduct } from "../api/products";
import { addSupplierToProduct, listProductSuppliers, listSuppliers } from "../api/suppliers";
import { ProductDetailPage } from "../pages/ProductDetailPage";

vi.mock("../api/products", () => ({
    getProduct: vi.fn(),
    listProductCategories: vi.fn(),
    updateProduct: vi.fn(),
}));

vi.mock("../api/suppliers", () => ({
    addSupplierToProduct: vi.fn(),
    listProductSuppliers: vi.fn(),
    listSuppliers: vi.fn(),
}));

const mockedGetProduct = vi.mocked(getProduct);
const mockedListProductCategories = vi.mocked(listProductCategories);
const mockedUpdateProduct = vi.mocked(updateProduct);
const mockedAddSupplierToProduct = vi.mocked(addSupplierToProduct);
const mockedListProductSuppliers = vi.mocked(listProductSuppliers);
const mockedListSuppliers = vi.mocked(listSuppliers);

function renderProductDetailPage() {
    return render(
        <MemoryRouter initialEntries={["/products/1"]}>
            <Routes>
                <Route path="/products/:productId" element={<ProductDetailPage />} />
            </Routes>
        </MemoryRouter>
    );
}

describe("ProductDetailPage", () => {
    beforeEach(() => {
        vi.clearAllMocks();

        mockedGetProduct.mockResolvedValue({
            id: 1,
            name: "Mini Split Install Kit",
            description: "Parts needed for a standard mini split installation.",
            cost_cents: 18000,
            unit_price_cents: 32500,
            category_id: 2,
            category_name: "Materials",
            is_active: true,
        });
        mockedUpdateProduct.mockResolvedValue({
            id: 1,
            name: "Updated Install Kit",
            description: "Parts needed for a standard mini split installation.",
            cost_cents: 19000,
            unit_price_cents: 35000,
            category_id: 3,
            category_name: "Parts",
            is_active: true,
        });
        mockedListProductCategories.mockResolvedValue([
            {
                id: 2,
                name: "Materials",
                description: null,
                is_active: true,
            },
            {
                id: 3,
                name: "Parts",
                description: null,
                is_active: true,
            },
        ]);
        mockedListProductSuppliers.mockResolvedValue([
            {
                id: 10,
                name: "Johnstone Supply",
                phone: "555-0100",
                email: "orders@example.com",
                website: "https://example.com",
                is_active: true,
            },
        ]);
        mockedListSuppliers.mockResolvedValue([
            {
                id: 10,
                name: "Johnstone Supply",
                phone: "555-0100",
                email: "orders@example.com",
                website: "https://example.com",
                is_active: true,
            },
            {
                id: 11,
                name: "Carrier Enterprise",
                phone: "555-0120",
                email: "orders@carrier.example",
                website: "https://carrier.example",
                is_active: true,
            },
        ]);
        mockedAddSupplierToProduct.mockResolvedValue({
            product_id: 1,
            supplier_id: 11,
            note: null,
            created_at: "2026-01-01",
            updated_at: "2026-01-01",
        });
    });

    it("renders product info, suppliers, and description sections", async () => {
        renderProductDetailPage();

        expect(await screen.findByRole("heading", { name: "Product Detail" })).toBeInTheDocument();
        expect(mockedGetProduct).toHaveBeenCalledWith(1);
        expect(mockedListProductSuppliers).toHaveBeenCalledWith(1);

        const productPanel = screen.getByRole("heading", { name: "Mini Split Install Kit" }).closest("section");
        expect(productPanel).not.toBeNull();
        expect(within(productPanel as HTMLElement).getByText("Category")).toBeInTheDocument();
        expect(within(productPanel as HTMLElement).getByText("Materials")).toBeInTheDocument();
        expect(within(productPanel as HTMLElement).getByText("Cost")).toBeInTheDocument();
        expect(within(productPanel as HTMLElement).getByText("$180")).toBeInTheDocument();
        expect(within(productPanel as HTMLElement).getByText("Sell")).toBeInTheDocument();
        expect(within(productPanel as HTMLElement).getByText("$325")).toBeInTheDocument();

        const suppliersPanel = screen.getByRole("heading", { name: "Suppliers" }).closest("section");
        expect(suppliersPanel).not.toBeNull();
        expect(within(suppliersPanel as HTMLElement).getByText("Johnstone Supply")).toBeInTheDocument();

        const descriptionPanel = screen.getByRole("heading", { name: "Description" }).closest("section");
        expect(descriptionPanel).not.toBeNull();
        expect(
            within(descriptionPanel as HTMLElement).getByText("Parts needed for a standard mini split installation."),
        ).toBeInTheDocument();
        expect(screen.getByRole("link", { name: "Back to products" })).toHaveAttribute("href", "/products");
    });

    it("updates the product info box", async () => {
        renderProductDetailPage();

        const productPanel = (await screen.findByRole("heading", { name: "Mini Split Install Kit" })).closest("section");
        expect(productPanel).not.toBeNull();

        fireEvent.click(within(productPanel as HTMLElement).getByRole("button", { name: "Edit" }));
        expect(await screen.findByRole("option", { name: "Parts" })).toBeInTheDocument();
        fireEvent.change(screen.getByLabelText("Name"), { target: { value: "Updated Install Kit" } });
        fireEvent.change(screen.getByLabelText("Category"), { target: { value: "3" } });
        fireEvent.change(screen.getByLabelText("Cost"), { target: { value: "190" } });
        fireEvent.change(screen.getByLabelText("Sell"), { target: { value: "350" } });
        fireEvent.click(screen.getByRole("button", { name: "Save" }));

        await waitFor(() => {
            expect(mockedUpdateProduct).toHaveBeenCalledWith(1, {
                name: "Updated Install Kit",
                category_id: 3,
                cost_cents: 19000,
                unit_price_cents: 35000,
            });
        });

        expect(await screen.findByRole("heading", { name: "Updated Install Kit" })).toBeInTheDocument();
        expect(screen.getByText("Parts")).toBeInTheDocument();
    });

    it("adds a supplier from the suppliers box", async () => {
        mockedListProductSuppliers
            .mockResolvedValueOnce([
                {
                    id: 10,
                    name: "Johnstone Supply",
                    phone: "555-0100",
                    email: "orders@example.com",
                    website: "https://example.com",
                    is_active: true,
                },
            ])
            .mockResolvedValueOnce([
                {
                    id: 10,
                    name: "Johnstone Supply",
                    phone: "555-0100",
                    email: "orders@example.com",
                    website: "https://example.com",
                    is_active: true,
                },
                {
                    id: 11,
                    name: "Carrier Enterprise",
                    phone: "555-0120",
                    email: "orders@carrier.example",
                    website: "https://carrier.example",
                    is_active: true,
                },
            ]);

        renderProductDetailPage();

        fireEvent.click(await screen.findByRole("button", { name: "Add Supplier" }));
        const dialog = await screen.findByRole("dialog", { name: "Add Supplier" });
        fireEvent.change(within(dialog).getByLabelText("Supplier"), { target: { value: "11" } });
        fireEvent.click(within(dialog).getByRole("button", { name: "Add Supplier" }));

        await waitFor(() => {
            expect(mockedAddSupplierToProduct).toHaveBeenCalledWith(1, { supplier_id: 11 });
        });

        expect(await screen.findByText("Carrier Enterprise")).toBeInTheDocument();
    });

    it("updates the product description box", async () => {
        mockedUpdateProduct.mockResolvedValueOnce({
            id: 1,
            name: "Mini Split Install Kit",
            description: "Updated install notes.",
            cost_cents: 18000,
            unit_price_cents: 32500,
            category_id: 2,
            category_name: "Materials",
            is_active: true,
        });

        renderProductDetailPage();

        const descriptionPanel = (await screen.findByRole("heading", { name: "Description" })).closest("section");
        expect(descriptionPanel).not.toBeNull();

        fireEvent.click(within(descriptionPanel as HTMLElement).getByRole("button", { name: "Edit" }));
        fireEvent.change(within(descriptionPanel as HTMLElement).getByLabelText("Description"), {
            target: { value: "Updated install notes." },
        });
        fireEvent.click(within(descriptionPanel as HTMLElement).getByRole("button", { name: "Save" }));

        await waitFor(() => {
            expect(mockedUpdateProduct).toHaveBeenCalledWith(1, {
                description: "Updated install notes.",
            });
        });

        expect(await screen.findByText("Updated install notes.")).toBeInTheDocument();
    });
});
