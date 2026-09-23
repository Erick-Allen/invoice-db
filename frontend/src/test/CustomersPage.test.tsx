import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter, useLocation } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { CustomersPage } from "../pages/CustomersPage";
import { createCustomer, createCustomerLocation, listCustomers, listLocations } from "../api/customers";

vi.mock("../api/customers", () => ({
    listCustomers: vi.fn(),
    listLocations: vi.fn(),
    createCustomer: vi.fn(),
    createCustomerLocation: vi.fn(),
    updateCustomer: vi.fn(),
    updateCustomerLocation: vi.fn(),
    deleteCustomer: vi.fn(),
}));

const mockedListCustomers = vi.mocked(listCustomers);
const mockedListLocations = vi.mocked(listLocations);
const mockedCreateCustomer = vi.mocked(createCustomer);
const mockedCreateCustomerLocation = vi.mocked(createCustomerLocation);

function LocationDisplay() {
    const location = useLocation();
    return <span data-testid="location-path">{location.pathname}</span>;
}

describe("CustomersPage", () => {
    beforeEach(() => {
        vi.clearAllMocks();

        mockedListCustomers.mockResolvedValue([
	            {
	                id: 1,
	                name: "John Doe",
	                email: "john@example.com",
	                phone: "4075550100",
	            },
        ]);
        mockedListLocations.mockResolvedValue([
            {
                id: 3,
                address_line1: "456 Existing Rd",
                address_line2: null,
                city: "Tampa",
                state: "FL",
                postal_code: "33602",
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
        ]);
        mockedCreateCustomer.mockResolvedValue({
            id: 2,
            name: "Jane Doe",
            email: "jane@example.com",
        });
        mockedCreateCustomerLocation.mockResolvedValue({
            id: 1,
            customer_id: 2,
            location_id: 1,
            label: "Primary",
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
    });

    it("renders the customer form and customer table", async () => {
        render(
            <MemoryRouter>
                <CustomersPage />
            </MemoryRouter>
        );

        expect(screen.getByRole("heading", { name: "Customers" })).toBeInTheDocument();
        expect(screen.queryByRole("dialog", { name: "Create Customer" })).not.toBeInTheDocument();

        expect(screen.getByRole("button", { name: "Create Customer" })).toBeInTheDocument();
        fireEvent.click(screen.getByRole("button", { name: "Create Customer" }));

        const dialog = screen.getByRole("dialog", { name: "Create Customer" });
        expect(within(dialog).getByLabelText("Name")).toBeInTheDocument();
        expect(within(dialog).getByLabelText("Email")).toBeInTheDocument();
        expect(within(dialog).getByLabelText("Existing Address")).toBeInTheDocument();
        expect(within(dialog).getByLabelText("New Location")).toBeInTheDocument();
        expect(within(dialog).queryByLabelText("Address")).not.toBeInTheDocument();

	        expect(await screen.findByText("John Doe")).toBeInTheDocument();
	        expect(screen.getByText("john@example.com")).toBeInTheDocument();
	        expect(screen.getByText("(407) 555-0100")).toBeInTheDocument();

        expect(screen.queryByRole("button", { name: "Edit" })).not.toBeInTheDocument();
        expect(screen.getByRole("button", { name: "Delete" })).toBeInTheDocument();
    });

    it("navigates to customer detail when a customer row is clicked", async () => {
        render(
            <MemoryRouter initialEntries={["/customers"]}>
                <CustomersPage />
                <LocationDisplay />
            </MemoryRouter>
        );

        fireEvent.click(await screen.findByRole("row", { name: /View John Doe/i }));

        expect(screen.getByTestId("location-path")).toHaveTextContent("/customers/1");
    });

    it("creates a primary location when provided in the customer form", async () => {
        render(
            <MemoryRouter>
                <CustomersPage />
            </MemoryRouter>
        );

        fireEvent.click(screen.getByRole("button", { name: "Create Customer" }));

	        const dialog = screen.getByRole("dialog", { name: "Create Customer" });
	        fireEvent.click(within(dialog).getByLabelText("New Location"));
	        fireEvent.change(within(dialog).getByLabelText("Name"), { target: { value: "Jane Doe" } });
	        fireEvent.change(within(dialog).getByLabelText("Email"), { target: { value: "jane@example.com" } });
	        fireEvent.change(within(dialog).getByLabelText("Phone"), { target: { value: "407-ABC-555-0100" } });
	        expect(within(dialog).getByLabelText("Phone")).toHaveValue("4075550100");
	        fireEvent.change(within(dialog).getByLabelText("Address"), { target: { value: "123 Main St" } });
        fireEvent.change(within(dialog).getByLabelText("City"), { target: { value: "Orlando" } });
        fireEvent.change(within(dialog).getByLabelText("State"), { target: { value: "FL" } });
        fireEvent.change(within(dialog).getByLabelText("ZIP Code"), { target: { value: "32801" } });
        fireEvent.click(within(dialog).getByRole("button", { name: "Create Customer" }));

	        await waitFor(() => {
	            expect(mockedCreateCustomer).toHaveBeenCalledWith({
	                name: "Jane Doe",
	                email: "jane@example.com",
	                phone: "4075550100",
	                customer_type: "residential",
	                company_name: null,
	            });
	            expect(mockedCreateCustomerLocation).toHaveBeenCalledWith(2, {
                label: "Primary",
                address_line1: "123 Main St",
                address_line2: null,
                city: "Orlando",
                state: "FL",
                postal_code: "32801",
                country: "US",
                is_primary: true,
                notes: null,
            });
        });
    });

	    it("creates a primary location from an existing location by default", async () => {
	        render(
	            <MemoryRouter>
	                <CustomersPage />
            </MemoryRouter>
        );

        fireEvent.click(screen.getByRole("button", { name: "Create Customer" }));

        const dialog = screen.getByRole("dialog", { name: "Create Customer" });
        fireEvent.change(within(dialog).getByLabelText("Name"), { target: { value: "Jane Doe" } });
        fireEvent.change(within(dialog).getByLabelText("Email"), { target: { value: "jane@example.com" } });
        expect(await within(dialog).findByText("456 Existing Rd, Tampa, FL 33602")).toBeInTheDocument();
        fireEvent.change(within(dialog).getByLabelText("Existing Address"), { target: { value: "3" } });
        fireEvent.click(within(dialog).getByRole("button", { name: "Create Customer" }));

        await waitFor(() => {
            expect(mockedCreateCustomerLocation).toHaveBeenCalledWith(2, {
                label: "Primary",
                address_line1: "456 Existing Rd",
                address_line2: null,
                city: "Tampa",
                state: "FL",
                postal_code: "33602",
                country: "US",
                is_primary: true,
                notes: null,
            });
	        });
	    });

	    it("requires customer phone numbers to be blank or 10 digits", async () => {
	        render(
	            <MemoryRouter>
	                <CustomersPage />
	            </MemoryRouter>
	        );

	        fireEvent.click(screen.getByRole("button", { name: "Create Customer" }));

	        const dialog = screen.getByRole("dialog", { name: "Create Customer" });
	        fireEvent.change(within(dialog).getByLabelText("Name"), { target: { value: "Jane Doe" } });
	        fireEvent.change(within(dialog).getByLabelText("Email"), { target: { value: "jane@example.com" } });
	        fireEvent.change(within(dialog).getByLabelText("Phone"), { target: { value: "555-0100" } });
	        fireEvent.click(within(dialog).getByRole("button", { name: "Create Customer" }));

	        expect(await screen.findByText("Customer phone must be exactly 10 digits.")).toBeInTheDocument();
	        expect(mockedCreateCustomer).not.toHaveBeenCalled();
	    });

	});
