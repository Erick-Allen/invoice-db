import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createCustomerLocation, getLocation, listCustomers, updateLocation } from "../api/customers";
import { createSupplierLocation, listSuppliers } from "../api/suppliers";
import { LocationDetailPage } from "../pages/LocationDetailPage";

vi.mock("../api/customers", () => ({
    createCustomerLocation: vi.fn(),
    getLocation: vi.fn(),
    listCustomers: vi.fn(),
    updateLocation: vi.fn(),
}));
vi.mock("../api/suppliers", () => ({
    createSupplierLocation: vi.fn(),
    listSuppliers: vi.fn(),
}));

const mockedCreateCustomerLocation = vi.mocked(createCustomerLocation);
const mockedGetLocation = vi.mocked(getLocation);
const mockedListCustomers = vi.mocked(listCustomers);
const mockedUpdateLocation = vi.mocked(updateLocation);
const mockedCreateSupplierLocation = vi.mocked(createSupplierLocation);
const mockedListSuppliers = vi.mocked(listSuppliers);

describe("LocationDetailPage", () => {
    beforeEach(() => {
        vi.clearAllMocks();

        mockedCreateCustomerLocation.mockResolvedValue({
            id: 10,
            customer_id: 1,
            location_id: 100,
            label: "Home",
            address_line1: "123 Main St",
            address_line2: null,
            city: "Orlando",
            state: "FL",
            postal_code: "32801",
            country: "US",
            is_primary: true,
            is_active: true,
            notes: null,
            created_at: "2026-01-01",
            updated_at: "2026-01-01",
        });
        mockedCreateSupplierLocation.mockResolvedValue({
            id: 20,
            supplier_id: 2,
            location_id: 100,
            label: "Counter",
            address_line1: "123 Main St",
            address_line2: null,
            city: "Orlando",
            state: "FL",
            postal_code: "32801",
            country: "US",
            is_primary: true,
            is_active: true,
            notes: null,
            created_at: "2026-01-01",
            updated_at: "2026-01-01",
        });
        mockedGetLocation.mockResolvedValue({
            location: {
                id: 100,
                address_line1: "123 Main St",
                address_line2: "Unit 12",
                city: "Orlando",
                state: "FL",
                postal_code: "32801",
                country: "US",
                assigned_customer_count: 1,
                assigned_customer_names: "John Doe",
                assigned_supplier_count: 0,
                assigned_supplier_names: null,
                assigned_count: 1,
                assigned_names: "John Doe",
                created_at: "2026-01-01",
                updated_at: "2026-01-01",
            },
            customer_assignments: [],
            supplier_assignments: [],
            invoices: [],
        });
        mockedListCustomers.mockResolvedValue([]);
        mockedListSuppliers.mockResolvedValue([]);
        mockedUpdateLocation.mockResolvedValue({
            id: 100,
            address_line1: "456 New Rd",
            address_line2: "Unit 12",
            city: "Winter Park",
            state: "FL",
            postal_code: "32789",
            country: "US",
            assigned_customer_count: 1,
            assigned_customer_names: "John Doe",
            assigned_supplier_count: 0,
            assigned_supplier_names: null,
            assigned_count: 1,
            assigned_names: "John Doe",
            created_at: "2026-01-01",
            updated_at: "2026-01-02",
        });
    });

    it("links back to the source customer when opened from customer detail", async () => {
        render(
            <MemoryRouter initialEntries={[{ pathname: "/locations/100", state: { fromCustomerId: 1 } }]}>
                <Routes>
                    <Route path="/locations/:locationId" element={<LocationDetailPage />} />
                </Routes>
            </MemoryRouter>
        );

        expect(await screen.findByRole("heading", { name: "Location Detail" })).toBeInTheDocument();
        expect(screen.getByRole("link", { name: "Back to customer" })).toHaveAttribute("href", "/customers/1");
        expect(screen.queryByText("Location ID")).not.toBeInTheDocument();
    });

    it("links back to the source invoice when opened from invoice detail", async () => {
        render(
            <MemoryRouter initialEntries={[{ pathname: "/locations/100", state: { fromInvoiceId: 7 } }]}>
                <Routes>
                    <Route path="/locations/:locationId" element={<LocationDetailPage />} />
                </Routes>
            </MemoryRouter>
        );

        expect(await screen.findByRole("heading", { name: "Location Detail" })).toBeInTheDocument();
        expect(screen.getByRole("link", { name: "Back to invoice" })).toHaveAttribute("href", "/invoices/7");
    });

    it("links back to locations without source context", async () => {
        render(
            <MemoryRouter initialEntries={["/locations/100"]}>
                <Routes>
                    <Route path="/locations/:locationId" element={<LocationDetailPage />} />
                </Routes>
            </MemoryRouter>
        );

        expect(await screen.findByRole("heading", { name: "Location Detail" })).toBeInTheDocument();
        expect(screen.getByRole("link", { name: "Back to locations" })).toHaveAttribute("href", "/locations");
    });

    it("assigns an active supplier to the current location", async () => {
        mockedListSuppliers.mockResolvedValue([
            {
                id: 2,
                name: "Johnstone",
                phone: "555-0100",
                email: "source@example.com",
                website: "https://example.com",
                is_active: true,
            },
        ]);

        render(
            <MemoryRouter initialEntries={["/locations/100"]}>
                <Routes>
                    <Route path="/locations/:locationId" element={<LocationDetailPage />} />
                </Routes>
            </MemoryRouter>
        );

        fireEvent.click(await screen.findByRole("button", { name: "Assign Supplier" }));
        const dialog = await screen.findByRole("dialog", { name: "Assign Supplier" });

        fireEvent.change(within(dialog).getByLabelText("Supplier"), { target: { value: "2" } });
        fireEvent.change(within(dialog).getByLabelText("Label"), { target: { value: "Counter" } });
        fireEvent.change(within(dialog).getByLabelText("Notes"), { target: { value: "Pickup desk" } });
        fireEvent.click(within(dialog).getByRole("button", { name: "Assign Supplier" }));

        await waitFor(() => {
            expect(mockedCreateSupplierLocation).toHaveBeenCalledWith(2, {
                label: "Counter",
                address_line1: "123 Main St",
                address_line2: "Unit 12",
                city: "Orlando",
                state: "FL",
                postal_code: "32801",
                country: "US",
                is_primary: false,
                notes: "Pickup desk",
            });
        });
    });

    it("updates the location address from location detail", async () => {
        render(
            <MemoryRouter initialEntries={["/locations/100"]}>
                <Routes>
                    <Route path="/locations/:locationId" element={<LocationDetailPage />} />
                </Routes>
            </MemoryRouter>
        );

        expect(await screen.findByText("123 Main St")).toBeInTheDocument();
        const addressBlock = screen.getByLabelText("Location address");
        expect(within(addressBlock).getByText("Address")).toBeInTheDocument();
        expect(within(addressBlock).getByText("Unit")).toBeInTheDocument();
        expect(screen.getByText("Unit 12")).toBeInTheDocument();
        expect(within(addressBlock).getByText("City")).toBeInTheDocument();
        expect(within(addressBlock).getByText("State")).toBeInTheDocument();
        expect(within(addressBlock).getByText("ZIP Code")).toBeInTheDocument();
        expect(within(addressBlock).getByText("Country")).toBeInTheDocument();
        expect(screen.getByText("Orlando")).toBeInTheDocument();
        expect(screen.getByText("FL")).toBeInTheDocument();
        expect(screen.getByText("32801")).toBeInTheDocument();
        expect(screen.getByText("US")).toBeInTheDocument();
        expect(screen.queryByText("Assigned To")).not.toBeInTheDocument();
        fireEvent.click(screen.getByRole("button", { name: "Edit" }));

        const dialog = await screen.findByRole("dialog", { name: "Edit Address" });
        expect(within(dialog).getByLabelText("Address")).toHaveValue("123 Main St");

        fireEvent.change(within(dialog).getByLabelText("Address"), { target: { value: "456 New Rd" } });
        fireEvent.change(within(dialog).getByLabelText("City"), { target: { value: "Winter Park" } });
        fireEvent.change(within(dialog).getByLabelText("ZIP code"), { target: { value: "32789" } });
        fireEvent.click(within(dialog).getByRole("button", { name: "Save Address" }));

        await waitFor(() => {
            expect(mockedUpdateLocation).toHaveBeenCalledWith(100, {
                address_line1: "456 New Rd",
                address_line2: "Unit 12",
                city: "Winter Park",
                state: "FL",
                postal_code: "32789",
                country: "US",
            });
        });
        expect(mockedGetLocation).toHaveBeenCalledTimes(2);
    });
});
