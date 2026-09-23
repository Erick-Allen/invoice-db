import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter, useLocation } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { listProducts } from "../api/products";
import {
    createSupplier,
    deactivateSupplier,
	    deleteSupplier,
	    listProductSuppliers,
	    listSuppliers,
	    removeSupplierFromProducts,
	    updateSupplier,
	} from "../api/suppliers";
import { SuppliersPage } from "../pages/SuppliersPage";

vi.mock("../api/products", () => ({
    listProducts: vi.fn(),
}));

vi.mock("../api/suppliers", () => ({
    listSuppliers: vi.fn(),
    createSupplier: vi.fn(),
    deactivateSupplier: vi.fn(),
    deleteSupplier: vi.fn(),
	    removeSupplierFromProducts: vi.fn(),
	    updateSupplier: vi.fn(),
	    listProductSuppliers: vi.fn(),
	}));

const mockedListProducts = vi.mocked(listProducts);
const mockedListSuppliers = vi.mocked(listSuppliers);
const mockedCreateSupplier = vi.mocked(createSupplier);
const mockedDeactivateSupplier = vi.mocked(deactivateSupplier);
const mockedDeleteSupplier = vi.mocked(deleteSupplier);
const mockedRemoveSupplierFromProducts = vi.mocked(removeSupplierFromProducts);
const mockedUpdateSupplier = vi.mocked(updateSupplier);
const mockedListProductSuppliers = vi.mocked(listProductSuppliers);

function LocationDisplay() {
    const location = useLocation();
    return <span data-testid="location-path">{location.pathname}</span>;
}

function renderSuppliersPage() {
    return render(
        <MemoryRouter initialEntries={["/suppliers"]}>
            <SuppliersPage />
            <LocationDisplay />
        </MemoryRouter>
    );
}

describe("SuppliersPage", () => {
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
        mockedCreateSupplier.mockResolvedValue({
            id: 2,
            name: "Home Depot",
            phone: null,
            email: null,
            website: null,
            is_active: true,
        });
        mockedDeactivateSupplier.mockResolvedValue({
            id: 1,
            name: "Johnstone Supply",
            phone: "555-0100",
            email: "orders@example.com",
            website: "https://example.com",
            is_active: false,
        });
	        mockedDeleteSupplier.mockResolvedValue(undefined);
	        mockedRemoveSupplierFromProducts.mockResolvedValue({ supplier_id: 1, removed_count: 1 });
	        mockedUpdateSupplier.mockResolvedValue({
	            id: 1,
	            name: "Johnstone Supply",
	            phone: "555-0100",
	            email: "orders@example.com",
	            website: "https://example.com",
	            is_active: true,
	        });
    });

    it("renders suppliers and creates a supplier", async () => {
        renderSuppliersPage();

        expect(screen.getByRole("heading", { name: "Suppliers" })).toBeInTheDocument();
        expect(await screen.findByText("Johnstone Supply")).toBeInTheDocument();
        expect(screen.getByRole("button", { name: "Create Supplier" })).toBeInTheDocument();

        fireEvent.click(screen.getByRole("button", { name: "Create Supplier" }));
        const dialog = screen.getByRole("dialog", { name: "Create Supplier" });
        fireEvent.change(within(dialog).getByLabelText("Name"), { target: { value: "Home Depot" } });
        fireEvent.change(within(dialog).getByLabelText("Phone"), { target: { value: "555-0120" } });
        fireEvent.change(within(dialog).getByLabelText("Email"), { target: { value: "orders@homedepot.test" } });
        fireEvent.change(within(dialog).getByLabelText("Website"), { target: { value: "https://homedepot.test" } });
        fireEvent.click(within(dialog).getByRole("button", { name: "Create Supplier" }));

        await waitFor(() => {
            expect(mockedCreateSupplier).toHaveBeenCalledWith({
                name: "Home Depot",
                phone: "555-0120",
                email: "orders@homedepot.test",
                website: "https://homedepot.test",
                is_active: true,
            });
        });
    });

    it("deactivates a supplier when it is linked to products", async () => {
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

        renderSuppliersPage();

        fireEvent.click(await screen.findByRole("button", { name: "Deactivate" }));

        await waitFor(() => {
            expect(mockedDeactivateSupplier).toHaveBeenCalledWith(1);
        });
    });

	    it("deletes a supplier when it is not linked to products", async () => {
	        renderSuppliersPage();

        fireEvent.click(await screen.findByRole("button", { name: "Delete" }));

        await waitFor(() => {
            expect(mockedDeleteSupplier).toHaveBeenCalledWith(1);
	        });
	    });

	    it("shows delete for inactive suppliers that are still linked to products", async () => {
	        mockedListSuppliers.mockResolvedValueOnce([
	            {
	                id: 1,
	                name: "Johnstone Supply",
	                phone: "555-0100",
	                email: "orders@example.com",
	                website: "https://example.com",
	                is_active: false,
	            },
	        ]);
	        mockedListProductSuppliers.mockResolvedValueOnce([
	            {
	                id: 1,
	                name: "Johnstone Supply",
	                phone: "555-0100",
	                email: "orders@example.com",
	                website: "https://example.com",
	                is_active: false,
	            },
	        ]);

	        renderSuppliersPage();

	        expect(await screen.findByRole("button", { name: "Activate" })).toBeInTheDocument();
	        fireEvent.click(screen.getByRole("button", { name: "Delete" }));

	        await waitFor(() => {
	            expect(mockedRemoveSupplierFromProducts).toHaveBeenCalledWith(1);
	        });
	    });

    it("navigates to supplier detail when a supplier row is clicked", async () => {
        renderSuppliersPage();

        fireEvent.click(await screen.findByRole("row", { name: /View Johnstone Supply/i }));

        expect(screen.getByTestId("location-path")).toHaveTextContent("/suppliers/1");
    });
});
