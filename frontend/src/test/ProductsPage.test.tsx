import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter, useLocation } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import {
    createProduct,
    createProductCategory,
    deactivateProduct,
    deactivateProductCategory,
    deleteProduct,
    deleteProductCategory,
    listProductCategories,
    listProducts,
    updateProductCategory,
} from "../api/products";
import { listProductSuppliers } from "../api/suppliers";
import { ProductsPage } from "../pages/ProductsPage";

vi.mock("../api/products", () => ({
    listProducts: vi.fn(),
    listProductCategories: vi.fn(),
    createProduct: vi.fn(),
    createProductCategory: vi.fn(),
    updateProduct: vi.fn(),
    updateProductCategory: vi.fn(),
    deactivateProduct: vi.fn(),
    deactivateProductCategory: vi.fn(),
    deleteProduct: vi.fn(),
    deleteProductCategory: vi.fn(),
}));

vi.mock("../api/suppliers", () => ({
    listProductSuppliers: vi.fn(),
}));

const mockedListProducts = vi.mocked(listProducts);
const mockedListProductCategories = vi.mocked(listProductCategories);
const mockedCreateProduct = vi.mocked(createProduct);
const mockedCreateProductCategory = vi.mocked(createProductCategory);
const mockedUpdateProductCategory = vi.mocked(updateProductCategory);
const mockedDeactivateProduct = vi.mocked(deactivateProduct);
const mockedDeactivateProductCategory = vi.mocked(deactivateProductCategory);
const mockedDeleteProduct = vi.mocked(deleteProduct);
const mockedDeleteProductCategory = vi.mocked(deleteProductCategory);
const mockedListProductSuppliers = vi.mocked(listProductSuppliers);

function LocationDisplay() {
    const location = useLocation();
    return <span data-testid="location-path">{location.pathname}</span>;
}

function renderProductsPage() {
    return render(
        <MemoryRouter initialEntries={["/products"]}>
            <ProductsPage />
            <LocationDisplay />
        </MemoryRouter>
    );
}

describe("ProductsPage", () => {
    beforeEach(() => {
        vi.clearAllMocks();
        vi.spyOn(window, "confirm").mockReturnValue(true);

        mockedListProducts.mockResolvedValue([
            {
                id: 1,
                name: "Consulting",
                description: "Hourly service",
                cost_cents: 0,
                unit_price_cents: 12500,
                category_id: 2,
                category_name: "Labor",
                is_active: true,
            },
        ]);
        mockedListProductCategories.mockResolvedValue([
            {
                id: 1,
                name: "Uncategorized",
                description: "Default category",
                is_active: true,
            },
            {
                id: 2,
                name: "Labor",
                description: "Billable work",
                is_active: true,
            },
        ]);
        mockedListProductSuppliers.mockResolvedValue([]);

        mockedCreateProduct.mockResolvedValue({
            id: 2,
            name: "Hosting",
            description: null,
            cost_cents: 2500,
            unit_price_cents: 5000,
            category_id: 1,
            category_name: "Uncategorized",
            is_active: true,
        });
        mockedCreateProductCategory.mockResolvedValue({
            id: 3,
            name: "Materials",
            description: null,
            is_active: true,
        });
        mockedUpdateProductCategory.mockResolvedValue({
            id: 2,
            name: "Updated Labor",
            description: "Updated category",
            is_active: true,
        });

        mockedDeactivateProduct.mockResolvedValue({
            id: 1,
            name: "Consulting",
            description: "Hourly service",
            cost_cents: 0,
            unit_price_cents: 12500,
            category_id: 2,
            category_name: "Labor",
            is_active: false,
        });
        mockedDeactivateProductCategory.mockResolvedValue({
            id: 2,
            name: "Labor",
            description: "Billable work",
            is_active: false,
        });

        mockedDeleteProduct.mockResolvedValue(undefined);
        mockedDeleteProductCategory.mockResolvedValue(undefined);
    });

    it("renders the product form and product table", async () => {
        renderProductsPage();

        expect(screen.getByRole("heading", { name: "Products", level: 2 })).toBeInTheDocument();
        expect(screen.getByRole("button", { name: "Create Product" })).toBeInTheDocument();
        expect(screen.queryByRole("dialog", { name: "Create Product" })).not.toBeInTheDocument();

        fireEvent.click(screen.getByRole("button", { name: "Create Product" }));

        expect(screen.getByRole("dialog", { name: "Create Product" })).toBeInTheDocument();
        const dialog = screen.getByRole("dialog", { name: "Create Product" });
        expect(within(dialog).getByLabelText("Name")).toBeInTheDocument();
        expect(within(dialog).getByLabelText("Description")).toBeInTheDocument();
        expect(within(dialog).getByLabelText("Cost")).toBeInTheDocument();
        expect(within(dialog).getByLabelText("Sell Price")).toBeInTheDocument();
        expect(within(dialog).getByLabelText("Category")).toBeInTheDocument();

        expect(await screen.findByText("Consulting")).toBeInTheDocument();
        expect(screen.getAllByText("Labor").length).toBeGreaterThan(0);
        expect(screen.getByText("Hourly service")).toBeInTheDocument();
        expect(screen.getByText("$125")).toBeInTheDocument();
        expect(screen.getByText("active")).toBeInTheDocument();
        expect(screen.queryByRole("button", { name: "Edit" })).not.toBeInTheDocument();
        expect(screen.queryByRole("button", { name: "Deactivate" })).not.toBeInTheDocument();
        expect(screen.getByRole("button", { name: "Delete" })).toBeInTheDocument();
    });

    it("creates a product with cents converted from dollars", async () => {
        renderProductsPage();

        expect(await screen.findByText("Consulting")).toBeInTheDocument();
        fireEvent.click(screen.getByRole("button", { name: "Create Product" }));

        fireEvent.change(screen.getByLabelText("Name"), { target: { value: "Hosting" } });
        fireEvent.change(screen.getByLabelText("Description"), { target: { value: "Monthly plan" } });
        fireEvent.change(screen.getByLabelText("Cost"), { target: { value: "25.00" } });
        fireEvent.change(screen.getByLabelText("Sell Price"), { target: { value: "50.25" } });

        const dialog = screen.getByRole("dialog", { name: "Create Product" });
        fireEvent.change(within(dialog).getByLabelText("Category"), { target: { value: "2" } });
        fireEvent.click(within(dialog).getByRole("button", { name: "Create Product" }));

        await waitFor(() => {
            expect(mockedCreateProduct).toHaveBeenCalledWith({
                name: "Hosting",
                description: "Monthly plan",
                cost_cents: 2500,
                unit_price_cents: 5025,
                category_id: 2,
                is_active: true,
            });
        });
    });

    it("navigates to product detail when a product row is clicked", async () => {
        renderProductsPage();

        fireEvent.click(await screen.findByRole("row", { name: /View Consulting/i }));

        expect(screen.getByTestId("location-path")).toHaveTextContent("/products/1");
    });

    it("navigates to category detail when a category row is clicked", async () => {
        renderProductsPage();

        fireEvent.click(await screen.findByRole("button", { name: "Categories" }));
        fireEvent.click(screen.getByRole("row", { name: /View category Labor/i }));

        expect(screen.getByTestId("location-path")).toHaveTextContent("/categories/2");
    });

    it("deactivates a product", async () => {
        mockedListProducts.mockResolvedValueOnce([
            {
                id: 1,
                name: "Consulting",
                description: "Hourly service",
                cost_cents: 0,
                unit_price_cents: 12500,
                category_id: 2,
                category_name: "Labor",
                is_active: true,
                invoice_item_count: 1,
                product_supplier_count: 0,
            },
        ]);
        renderProductsPage();

        fireEvent.click(await screen.findByRole("button", { name: "Deactivate" }));

        await waitFor(() => {
            expect(mockedDeactivateProduct).toHaveBeenCalledWith(1);
        });
    });

    it("deletes a product after confirmation", async () => {
        renderProductsPage();

        fireEvent.click(await screen.findByRole("button", { name: "Delete" }));

        await waitFor(() => {
            expect(mockedDeleteProduct).toHaveBeenCalledWith(1);
        });
    });

    it("loads active-only products when the filter is checked", async () => {
        renderProductsPage();

        fireEvent.click(await screen.findByLabelText("Active only"));

        await waitFor(() => {
            expect(mockedListProducts).toHaveBeenLastCalledWith(true);
        });
    });

    it("creates and deactivates product categories", async () => {
        renderProductsPage();

        fireEvent.click(await screen.findByRole("button", { name: "Categories" }));
        fireEvent.click(screen.getByRole("button", { name: "Create Category" }));
        fireEvent.change(screen.getByLabelText("Name"), { target: { value: "Materials" } });
        fireEvent.change(screen.getByLabelText("Description"), { target: { value: "Physical goods" } });
        fireEvent.click(within(screen.getByRole("dialog", { name: "Create Category" })).getByRole("button", { name: "Create Category" }));

        await waitFor(() => {
            expect(mockedCreateProductCategory).toHaveBeenCalledWith({
                name: "Materials",
                description: "Physical goods",
                is_active: true,
            });
        });

        fireEvent.click(screen.getByRole("button", { name: "Deactivate" }));

        await waitFor(() => {
            expect(mockedDeactivateProductCategory).toHaveBeenCalledWith(2);
        });
    });

    it("updates a product category", async () => {
        renderProductsPage();

        fireEvent.click(await screen.findByRole("button", { name: "Categories" }));
        expect(screen.getAllByRole("button", { name: "Edit" })).toHaveLength(1);

        fireEvent.click(screen.getByRole("button", { name: "Edit" }));
        fireEvent.change(screen.getByDisplayValue("Labor"), { target: { value: "Updated Labor" } });
        fireEvent.click(screen.getByRole("button", { name: "Save" }));

        await waitFor(() => {
            expect(mockedUpdateProductCategory).toHaveBeenCalledWith(
                2,
                expect.objectContaining({
                    name: "Updated Labor",
                    is_active: true,
                }),
            );
        });
    });

    it("deletes a product category after confirmation", async () => {
        mockedListProductCategories.mockResolvedValueOnce([
            {
                id: 1,
                name: "Uncategorized",
                description: "Default category",
                is_active: true,
            },
            {
                id: 2,
                name: "Labor",
                description: "Billable work",
                is_active: true,
            },
            {
                id: 3,
                name: "Unused",
                description: null,
                is_active: true,
            },
        ]);
        renderProductsPage();

        fireEvent.click(await screen.findByRole("button", { name: "Categories" }));
        fireEvent.click(screen.getByRole("button", { name: "Delete" }));

        await waitFor(() => {
            expect(mockedDeleteProductCategory).toHaveBeenCalledWith(3);
        });
    });

    it("displays product suppliers without inline assignment controls", async () => {
        mockedListProductSuppliers.mockResolvedValueOnce([
            {
                id: 1,
                name: "Johnstone Supply",
                phone: "555-0100",
                email: "orders@example.com",
                website: "https://example.com",
                is_active: true,
            },
        ]);

        renderProductsPage();

        expect(await screen.findByText("Johnstone Supply")).toBeInTheDocument();
        expect(screen.queryByLabelText("Supplier for Consulting")).not.toBeInTheDocument();
        expect(screen.queryByRole("button", { name: "Add" })).not.toBeInTheDocument();
        expect(screen.queryByRole("button", { name: "Remove Johnstone Supply from Consulting" })).not.toBeInTheDocument();
    });
});
