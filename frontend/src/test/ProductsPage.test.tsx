import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
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
} from "../api/products";
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

describe("ProductsPage", () => {
    beforeEach(() => {
        vi.clearAllMocks();
        vi.spyOn(window, "confirm").mockReturnValue(true);

        mockedListProducts.mockResolvedValue([
            {
                id: 1,
                name: "Consulting",
                description: "Hourly service",
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

        mockedCreateProduct.mockResolvedValue({
            id: 2,
            name: "Hosting",
            description: null,
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

        mockedUpdateProduct.mockResolvedValue({
            id: 1,
            name: "Updated Consulting",
            description: "Updated service",
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

        mockedDeactivateProduct.mockResolvedValue({
            id: 1,
            name: "Consulting",
            description: "Hourly service",
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
        expect(within(dialog).getByLabelText("Unit Price")).toBeInTheDocument();
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
        fireEvent.change(screen.getByLabelText("Unit Price"), { target: { value: "50.25" } });

        const dialog = screen.getByRole("dialog", { name: "Create Product" });
        fireEvent.change(within(dialog).getByLabelText("Category"), { target: { value: "2" } });
        fireEvent.click(within(dialog).getByRole("button", { name: "Create Product" }));

        await waitFor(() => {
            expect(mockedCreateProduct).toHaveBeenCalledWith({
                name: "Hosting",
                description: "Monthly plan",
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
        fireEvent.change(screen.getByDisplayValue("125.00"), { target: { value: "150.00" } });
        fireEvent.click(screen.getByRole("button", { name: "Save" }));

        await waitFor(() => {
            expect(mockedUpdateProduct).toHaveBeenCalledWith(
                1,
                expect.objectContaining({
                    name: "Updated Consulting",
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
});
