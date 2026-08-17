import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
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
    updateProduct,
    updateProductCategory,
} from "../api/products";
import {
    addSupplierToProduct,
    createSupplier,
    deactivateSupplier,
    deleteSupplier,
    listProductSuppliers,
    listSuppliers,
    removeSupplierFromProduct,
    removeSupplierFromProducts,
    updateSupplier,
} from "../api/suppliers";
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
    listSuppliers: vi.fn(),
    createSupplier: vi.fn(),
    updateSupplier: vi.fn(),
    deactivateSupplier: vi.fn(),
    deleteSupplier: vi.fn(),
    removeSupplierFromProducts: vi.fn(),
    listProductSuppliers: vi.fn(),
    addSupplierToProduct: vi.fn(),
    removeSupplierFromProduct: vi.fn(),
}));

const mockedListProducts = vi.mocked(listProducts);
const mockedListProductCategories = vi.mocked(listProductCategories);
const mockedCreateProduct = vi.mocked(createProduct);
const mockedCreateProductCategory = vi.mocked(createProductCategory);
const mockedUpdateProduct = vi.mocked(updateProduct);
const mockedUpdateProductCategory = vi.mocked(updateProductCategory);
const mockedDeactivateProduct = vi.mocked(deactivateProduct);
const mockedDeactivateProductCategory = vi.mocked(deactivateProductCategory);
const mockedDeleteProduct = vi.mocked(deleteProduct);
const mockedDeleteProductCategory = vi.mocked(deleteProductCategory);
const mockedListSuppliers = vi.mocked(listSuppliers);
const mockedCreateSupplier = vi.mocked(createSupplier);
const mockedUpdateSupplier = vi.mocked(updateSupplier);
const mockedDeactivateSupplier = vi.mocked(deactivateSupplier);
const mockedDeleteSupplier = vi.mocked(deleteSupplier);
const mockedRemoveSupplierFromProducts = vi.mocked(removeSupplierFromProducts);
const mockedListProductSuppliers = vi.mocked(listProductSuppliers);
const mockedAddSupplierToProduct = vi.mocked(addSupplierToProduct);
const mockedRemoveSupplierFromProduct = vi.mocked(removeSupplierFromProduct);

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
        mockedListSuppliers.mockResolvedValue([
            {
                id: 1,
                name: "Johnstone Supply",
                phone: "555-0100",
                email: "orders@example.com",
                website: "https://example.com",
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
        mockedCreateSupplier.mockResolvedValue({
            id: 2,
            name: "Home Depot",
            phone: null,
            email: null,
            website: null,
            is_active: true,
        });

        mockedUpdateProduct.mockResolvedValue({
            id: 1,
            name: "Updated Consulting",
            description: "Updated service",
            cost_cents: 5000,
            unit_price_cents: 15000,
            category_id: 2,
            category_name: "Labor",
            is_active: true,
        });
        mockedUpdateProductCategory.mockResolvedValue({
            id: 2,
            name: "Updated Labor",
            description: "Updated category",
            is_active: true,
        });
        mockedUpdateSupplier.mockResolvedValue({
            id: 1,
            name: "Updated Supplier",
            phone: "555-0101",
            email: "updated@example.com",
            website: "https://supplier.example.com",
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
        mockedDeactivateSupplier.mockResolvedValue({
            id: 1,
            name: "Johnstone Supply",
            phone: "555-0100",
            email: "orders@example.com",
            website: "https://example.com",
            is_active: false,
        });

        mockedDeleteProduct.mockResolvedValue(undefined);
        mockedDeleteProductCategory.mockResolvedValue(undefined);
        mockedDeleteSupplier.mockResolvedValue(undefined);
        mockedRemoveSupplierFromProducts.mockResolvedValue({ supplier_id: 1, removed_count: 1 });
        mockedAddSupplierToProduct.mockResolvedValue({
            product_id: 1,
            supplier_id: 1,
            note: null,
            created_at: "2026-01-01T00:00:00",
            updated_at: "2026-01-01T00:00:00",
        });
        mockedRemoveSupplierFromProduct.mockResolvedValue(undefined);
    });

    it("renders the product form and product table", async () => {
        render(<ProductsPage />);

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
        expect(screen.getByText("$125.00")).toBeInTheDocument();
        expect(screen.getByText("active")).toBeInTheDocument();
        expect(screen.getByRole("button", { name: "Edit" })).toBeInTheDocument();
        expect(screen.getByRole("button", { name: "Deactivate" })).toBeInTheDocument();
        expect(screen.getByRole("button", { name: "Delete" })).toBeInTheDocument();
    });

    it("creates a product with cents converted from dollars", async () => {
        render(<ProductsPage />);

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

    it("updates a product", async () => {
        render(<ProductsPage />);

        fireEvent.click(await screen.findByRole("button", { name: "Edit" }));
        fireEvent.change(screen.getByDisplayValue("Consulting"), { target: { value: "Updated Consulting" } });
        fireEvent.change(screen.getByDisplayValue("0.00"), { target: { value: "50.00" } });
        fireEvent.change(screen.getByDisplayValue("125.00"), { target: { value: "150.00" } });
        fireEvent.click(screen.getByRole("button", { name: "Save" }));

        await waitFor(() => {
            expect(mockedUpdateProduct).toHaveBeenCalledWith(
                1,
                expect.objectContaining({
                    name: "Updated Consulting",
                    cost_cents: 5000,
                    unit_price_cents: 15000,
                    category_id: 2,
                }),
            );
        });
    });

    it("deactivates a product", async () => {
        render(<ProductsPage />);

        fireEvent.click(await screen.findByRole("button", { name: "Deactivate" }));

        await waitFor(() => {
            expect(mockedDeactivateProduct).toHaveBeenCalledWith(1);
        });
    });

    it("deletes a product after confirmation", async () => {
        render(<ProductsPage />);

        fireEvent.click(await screen.findByRole("button", { name: "Delete" }));

        await waitFor(() => {
            expect(mockedDeleteProduct).toHaveBeenCalledWith(1);
        });
    });

    it("loads active-only products when the filter is checked", async () => {
        render(<ProductsPage />);

        fireEvent.click(await screen.findByLabelText("Active only"));

        await waitFor(() => {
            expect(mockedListProducts).toHaveBeenLastCalledWith(true);
        });
    });

    it("creates and deactivates product categories", async () => {
        render(<ProductsPage />);

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
        render(<ProductsPage />);

        fireEvent.click(await screen.findByRole("button", { name: "Categories" }));
        fireEvent.click(screen.getAllByRole("button", { name: "Edit" })[1]);
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
        render(<ProductsPage />);

        fireEvent.click(await screen.findByRole("button", { name: "Categories" }));
        fireEvent.click(screen.getByRole("button", { name: "Delete" }));

        await waitFor(() => {
            expect(mockedDeleteProductCategory).toHaveBeenCalledWith(2);
        });
    });

    it("creates and deactivates suppliers from the supplier tab", async () => {
        render(<ProductsPage />);

        fireEvent.click(await screen.findByRole("button", { name: "Suppliers" }));
        fireEvent.click(screen.getByRole("button", { name: "Create Supplier" }));
        fireEvent.change(screen.getByLabelText("Name"), { target: { value: "Home Depot" } });
        fireEvent.change(screen.getByLabelText("Phone"), { target: { value: "555-0120" } });
        fireEvent.change(screen.getByLabelText("Email"), { target: { value: "orders@homedepot.test" } });
        fireEvent.change(screen.getByLabelText("Website"), { target: { value: "https://homedepot.test" } });
        fireEvent.click(within(screen.getByRole("dialog", { name: "Create Supplier" })).getByRole("button", { name: "Create Supplier" }));

        await waitFor(() => {
            expect(mockedCreateSupplier).toHaveBeenCalledWith({
                name: "Home Depot",
                phone: "555-0120",
                email: "orders@homedepot.test",
                website: "https://homedepot.test",
                is_active: true,
            });
        });

        fireEvent.click(screen.getByRole("button", { name: "Deactivate" }));

        await waitFor(() => {
            expect(mockedDeactivateSupplier).toHaveBeenCalledWith(1);
        });
    });

    it("adds and removes a supplier on a product row", async () => {
        mockedListProductSuppliers
            .mockResolvedValueOnce([])
            .mockResolvedValueOnce([
                {
                    id: 1,
                    name: "Johnstone Supply",
                    phone: "555-0100",
                    email: "orders@example.com",
                    website: "https://example.com",
                    is_active: true,
                },
            ]);

        render(<ProductsPage />);

        fireEvent.change(await screen.findByLabelText("Supplier for Consulting"), { target: { value: "1" } });
        fireEvent.click(screen.getByRole("button", { name: "Add" }));

        await waitFor(() => {
            expect(mockedAddSupplierToProduct).toHaveBeenCalledWith(1, { supplier_id: 1 });
        });

        await waitFor(() => {
            expect(screen.getByText("Johnstone Supply")).toBeInTheDocument();
        });

        fireEvent.click(screen.getByRole("button", { name: "Remove Johnstone Supply from Consulting" }));

        await waitFor(() => {
            expect(mockedRemoveSupplierFromProduct).toHaveBeenCalledWith(1, 1);
        });
    });
});
