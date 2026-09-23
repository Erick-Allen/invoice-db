import { fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import {
    getSupplier,
    listSupplierLocations,
    listSupplierProducts,
} from "../api/suppliers";
import { SupplierDetailPage } from "../pages/SupplierDetailPage";

vi.mock("../api/suppliers", () => ({
    getSupplier: vi.fn(),
    listSupplierLocations: vi.fn(),
    listSupplierProducts: vi.fn(),
}));

const mockedGetSupplier = vi.mocked(getSupplier);
const mockedListSupplierLocations = vi.mocked(listSupplierLocations);
const mockedListSupplierProducts = vi.mocked(listSupplierProducts);

function LocationDisplay() {
    const location = useLocation();
    return <span data-testid="location-path">{location.pathname}</span>;
}

function renderSupplierDetailPage() {
    return render(
        <MemoryRouter initialEntries={["/suppliers/1"]}>
            <Routes>
                <Route path="/suppliers/:supplierId" element={<SupplierDetailPage />} />
            </Routes>
            <LocationDisplay />
        </MemoryRouter>
    );
}

describe("SupplierDetailPage", () => {
    beforeEach(() => {
        vi.clearAllMocks();

        mockedGetSupplier.mockResolvedValue({
            id: 1,
            name: "Johnstone Supply",
            phone: "555-0100",
            email: "orders@example.com",
            website: "https://example.com",
            is_active: true,
        });
        mockedListSupplierLocations.mockResolvedValue([
            {
                id: 10,
                supplier_id: 1,
                location_id: 100,
                label: "Counter",
                address_line1: "123 Supply Rd",
                address_line2: "Unit 4",
                city: "Orlando",
                state: "FL",
                postal_code: "32801",
                country: "US",
                is_primary: true,
                is_active: true,
                notes: "Pickup desk",
                created_at: "2026-01-01",
                updated_at: "2026-01-01",
            },
        ]);
        mockedListSupplierProducts.mockResolvedValue([
            {
                id: 2,
                name: "Line Set",
                description: "Copper line set",
                cost_cents: 8000,
                unit_price_cents: 12500,
                category_id: 3,
                category_name: "Materials",
                is_active: true,
            },
        ]);
    });

    it("renders supplier info, locations, and products", async () => {
        renderSupplierDetailPage();

        expect(await screen.findByRole("heading", { name: "Supplier Detail" })).toBeInTheDocument();
        expect(mockedGetSupplier).toHaveBeenCalledWith(1);
        expect(mockedListSupplierLocations).toHaveBeenCalledWith(1);
        expect(mockedListSupplierProducts).toHaveBeenCalledWith(1);

        const supplierPanel = screen.getByRole("heading", { name: "Johnstone Supply" }).closest("section");
        expect(supplierPanel).not.toBeNull();
        expect(within(supplierPanel as HTMLElement).getByText("555-0100")).toBeInTheDocument();
        expect(within(supplierPanel as HTMLElement).getByText("orders@example.com")).toBeInTheDocument();

        const locationsPanel = screen.getByRole("heading", { name: "Locations" }).closest("section");
        expect(locationsPanel).not.toBeNull();
        expect(within(locationsPanel as HTMLElement).getByText("Counter")).toBeInTheDocument();
        expect(within(locationsPanel as HTMLElement).getByText("123 Supply Rd, Unit 4, Orlando, FL 32801")).toBeInTheDocument();

        const productsPanel = screen.getByRole("heading", { name: "Products" }).closest("section");
        expect(productsPanel).not.toBeNull();
        expect(within(productsPanel as HTMLElement).getByText("Line Set")).toBeInTheDocument();
        expect(within(productsPanel as HTMLElement).getByText("$80")).toBeInTheDocument();
        expect(within(productsPanel as HTMLElement).getByText("$125")).toBeInTheDocument();
        expect(screen.getByRole("link", { name: "Back to suppliers" })).toHaveAttribute("href", "/suppliers");
    });

    it("opens location detail from the locations table", async () => {
        renderSupplierDetailPage();

        fireEvent.click(await screen.findByRole("row", { name: /View Counter/i }));
        expect(screen.getByTestId("location-path")).toHaveTextContent("/locations/100");
    });

    it("opens product detail from the products table", async () => {
        renderSupplierDetailPage();

        fireEvent.click(await screen.findByRole("row", { name: /View Line Set/i }));
        expect(screen.getByTestId("location-path")).toHaveTextContent("/products/2");
    });
});
