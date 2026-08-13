import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import {
    createProduct,
    deactivateProduct,
    deleteProduct,
    listProducts,
    updateProduct,
} from "../api/products";
import { ProductsPage } from "../pages/ProductsPage";

vi.mock("../api/products", () => ({
    listProducts: vi.fn(),
    createProduct: vi.fn(),
    updateProduct: vi.fn(),
    deactivateProduct: vi.fn(),
    deleteProduct: vi.fn(),
}));

const mockedListProducts = vi.mocked(listProducts);
const mockedCreateProduct = vi.mocked(createProduct);
const mockedUpdateProduct = vi.mocked(updateProduct);
const mockedDeactivateProduct = vi.mocked(deactivateProduct);
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
                is_active: true,
            },
        ]);

        mockedCreateProduct.mockResolvedValue({
            id: 2,
            name: "Hosting",
            description: null,
            unit_price_cents: 5000,
            is_active: true,
        });

        mockedUpdateProduct.mockResolvedValue({
            id: 1,
            name: "Updated Consulting",
            description: "Updated service",
            unit_price_cents: 15000,
            is_active: true,
        });

        mockedDeactivateProduct.mockResolvedValue({
            id: 1,
            name: "Consulting",
            description: "Hourly service",
            unit_price_cents: 12500,
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
        expect(screen.getByLabelText("Name")).toBeInTheDocument();
        expect(screen.getByLabelText("Description")).toBeInTheDocument();
        expect(screen.getByLabelText("Unit Price")).toBeInTheDocument();

        expect(await screen.findByText("Consulting")).toBeInTheDocument();
        expect(screen.getByText("Hourly service")).toBeInTheDocument();
        expect(screen.getByText("$125.00")).toBeInTheDocument();
        expect(screen.getByText("active")).toBeInTheDocument();
        expect(screen.getByRole("button", { name: /Actions/i })).toBeInTheDocument();
        expect(screen.queryByRole("menuitem", { name: "Edit" })).not.toBeInTheDocument();

        fireEvent.click(screen.getByRole("button", { name: /Actions/i }));

        expect(screen.getByRole("menuitem", { name: "Edit" })).toBeInTheDocument();
        expect(screen.getByRole("menuitem", { name: "Deactivate" })).toBeInTheDocument();
        expect(screen.getByRole("menuitem", { name: "Delete" })).toBeInTheDocument();
    });

    it("creates a product with cents converted from dollars", async () => {
        render(<ProductsPage />);

        fireEvent.click(screen.getByRole("button", { name: "Create Product" }));

        fireEvent.change(screen.getByLabelText("Name"), { target: { value: "Hosting" } });
        fireEvent.change(screen.getByLabelText("Description"), { target: { value: "Monthly plan" } });
        fireEvent.change(screen.getByLabelText("Unit Price"), { target: { value: "50.25" } });

        const dialog = screen.getByRole("dialog", { name: "Create Product" });
        fireEvent.click(within(dialog).getByRole("button", { name: "Create Product" }));

        await waitFor(() => {
            expect(mockedCreateProduct).toHaveBeenCalledWith({
                name: "Hosting",
                description: "Monthly plan",
                unit_price_cents: 5025,
                is_active: true,
            });
        });
    });

    it("updates a product", async () => {
        render(<ProductsPage />);

        fireEvent.click(await screen.findByRole("button", { name: /Actions/i }));
        fireEvent.click(screen.getByRole("menuitem", { name: "Edit" }));
        fireEvent.change(screen.getByDisplayValue("Consulting"), { target: { value: "Updated Consulting" } });
        fireEvent.change(screen.getByDisplayValue("125.00"), { target: { value: "150.00" } });
        fireEvent.click(screen.getByRole("button", { name: "Save" }));

        await waitFor(() => {
            expect(mockedUpdateProduct).toHaveBeenCalledWith(
                1,
                expect.objectContaining({
                    name: "Updated Consulting",
                    unit_price_cents: 15000,
                }),
            );
        });
    });

    it("deactivates a product", async () => {
        render(<ProductsPage />);

        fireEvent.click(await screen.findByRole("button", { name: /Actions/i }));
        fireEvent.click(screen.getByRole("menuitem", { name: "Deactivate" }));

        await waitFor(() => {
            expect(mockedDeactivateProduct).toHaveBeenCalledWith(1);
        });
    });

    it("deletes a product after confirmation", async () => {
        render(<ProductsPage />);

        fireEvent.click(await screen.findByRole("button", { name: /Actions/i }));
        fireEvent.click(screen.getByRole("menuitem", { name: "Delete" }));

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
});
