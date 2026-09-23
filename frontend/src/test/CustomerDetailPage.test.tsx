import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createCustomerLocation, deleteCustomerLocation, getCustomer, listCustomerLocations, listLocations, updateCustomer, updateCustomerLocation } from "../api/customers";
import { createInvoice, listInvoices } from "../api/invoices";
import { getPaymentSummary } from "../api/payments";
import { CustomerDetailPage } from "../pages/CustomerDetailPage";

vi.mock("../api/customers", () => ({
    createCustomerLocation: vi.fn(),
    deleteCustomerLocation: vi.fn(),
    getCustomer: vi.fn(),
    listCustomerLocations: vi.fn(),
    listLocations: vi.fn(),
    updateCustomer: vi.fn(),
    updateCustomerLocation: vi.fn(),
}));

vi.mock("../api/invoices", () => ({
    createInvoice: vi.fn(),
    listInvoices: vi.fn(),
}));

vi.mock("../api/payments", () => ({
    getPaymentSummary: vi.fn(),
}));

const mockedCreateCustomerLocation = vi.mocked(createCustomerLocation);
const mockedGetCustomer = vi.mocked(getCustomer);
const mockedListCustomerLocations = vi.mocked(listCustomerLocations);
const mockedListLocations = vi.mocked(listLocations);
const mockedUpdateCustomer = vi.mocked(updateCustomer);
const mockedUpdateCustomerLocation = vi.mocked(updateCustomerLocation);
const mockedDeleteCustomerLocation = vi.mocked(deleteCustomerLocation);
const mockedCreateInvoice = vi.mocked(createInvoice);
const mockedListInvoices = vi.mocked(listInvoices);
const mockedGetPaymentSummary = vi.mocked(getPaymentSummary);

function LocationDisplay() {
    const location = useLocation();
    const state = location.state as { fromCustomerId?: number; fromInvoiceId?: number } | null;
    return (
        <>
            <span data-testid="location-path">{location.pathname}</span>
            <span data-testid="location-state">{state?.fromCustomerId ?? ""}</span>
            <span data-testid="invoice-state">{state?.fromInvoiceId ?? ""}</span>
        </>
    );
}

describe("CustomerDetailPage", () => {
    beforeEach(() => {
        vi.clearAllMocks();

	        mockedGetCustomer.mockResolvedValue({
	            id: 1,
	            name: "John Doe",
	            email: "john@example.com",
	            phone: "4075550100",
	        });
        mockedUpdateCustomer.mockResolvedValue({
	            id: 1,
	            name: "John Smith",
	            email: "john.smith@example.com",
	            phone: "4075550101",
	            customer_type: "commercial",
	            company_name: "Smith HVAC",
	        });
        mockedListCustomerLocations.mockResolvedValue([
            {
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
            },
        ]);
        mockedListLocations.mockResolvedValue([]);
        mockedCreateCustomerLocation.mockResolvedValue({
            id: 1,
            customer_id: 1,
            location_id: 1,
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
        mockedUpdateCustomerLocation.mockResolvedValue({
            id: 1,
            customer_id: 1,
            location_id: 1,
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
        mockedDeleteCustomerLocation.mockResolvedValue(undefined);
        mockedCreateInvoice.mockResolvedValue({
            id: 55,
            customer_id: 1,
            location_id: 10,
            date_issued: "2026-09-21",
            date_due: "2026-10-21",
            total: 0,
            status: "draft",
        });
        mockedListInvoices.mockResolvedValue([
            {
                id: 2,
                customer_id: 1,
                date_issued: "2026-06-01",
                date_due: "2026-07-01",
                total: 2500,
                cost_total_cents: 1000,
                profit_total_cents: 1500,
                status: "paid",
            },
            {
                id: 1,
                customer_id: 1,
                date_issued: "2026-05-01",
                date_due: "2026-06-01",
                total: 5000,
                cost_total_cents: 2000,
                profit_total_cents: 3000,
                status: "sent",
            },
            {
                id: 3,
                customer_id: 1,
                date_issued: "2026-07-01",
                date_due: "2026-08-01",
                total: 10000,
                cost_total_cents: 4000,
                profit_total_cents: 6000,
                status: "draft",
            },
        ]);
        mockedGetPaymentSummary.mockImplementation(async (invoiceId: number) => ({
            invoice_id: invoiceId,
            invoice_total_cents: invoiceId === 1 ? 5000 : invoiceId === 2 ? 2500 : 10000,
            amount_paid_cents: invoiceId === 1 ? 1500 : invoiceId === 2 ? 2500 : 0,
            balance_due_cents: invoiceId === 1 ? 3500 : invoiceId === 2 ? 0 : 10000,
            is_paid: invoiceId === 2,
        }));
    });

    it("renders customer detail with invoice summary and history", async () => {
        render(
            <MemoryRouter initialEntries={["/customers/1"]}>
                <Routes>
                    <Route path="/customers/:customerId" element={<><CustomerDetailPage /><LocationDisplay /></>} />
                </Routes>
            </MemoryRouter>
        );

        expect(await screen.findByRole("heading", { name: "John Doe" })).toBeInTheDocument();
        expect(screen.getByText("john@example.com")).toBeInTheDocument();
        expect(screen.getByRole("link", { name: "Back to customers" })).toBeInTheDocument();
        expect(mockedGetCustomer).toHaveBeenCalledWith(1);
        expect(mockedListInvoices).toHaveBeenCalledWith({ customerId: 1, includeItems: true });
        expect(mockedGetPaymentSummary).toHaveBeenCalledWith(1);
        expect(mockedGetPaymentSummary).toHaveBeenCalledWith(2);

        const summary = screen.getByLabelText("Customer invoice summary");
        expect(within(summary).getByText("Invoices")).toBeInTheDocument();
        expect(within(summary).getByText("3")).toBeInTheDocument();
        expect(within(summary).getByText("$75")).toBeInTheDocument();
        expect(within(summary).getByText("$40")).toBeInTheDocument();
        expect(within(summary).getByText("$30")).toBeInTheDocument();
        expect(within(summary).getByText("$10")).toBeInTheDocument();
        expect(within(summary).queryByText("-$30")).not.toBeInTheDocument();
        expect(within(summary).getByText("$35")).toBeInTheDocument();

        const firstInvoiceRow = screen.getByRole("row", { name: /View invoice 1/i });
        const secondInvoiceRow = screen.getByRole("row", { name: /View invoice 2/i });
        expect(within(firstInvoiceRow).getByText("#1")).toBeInTheDocument();
        expect(within(secondInvoiceRow).getByText("#2")).toBeInTheDocument();
        expect(within(firstInvoiceRow).getByText("sent")).toBeInTheDocument();
        expect(within(secondInvoiceRow).getByText("paid")).toBeInTheDocument();
    });

    it("links back to the source invoice when opened from invoice detail", async () => {
        render(
            <MemoryRouter initialEntries={[{ pathname: "/customers/1", state: { fromInvoiceId: 7 } }]}>
                <Routes>
                    <Route path="/customers/:customerId" element={<CustomerDetailPage />} />
                </Routes>
            </MemoryRouter>
        );

        expect(await screen.findByRole("heading", { name: "John Doe" })).toBeInTheDocument();
        expect(screen.getByRole("link", { name: "Back to invoice" })).toHaveAttribute("href", "/invoices/7");
    });

    it("edits customer information from the detail page", async () => {
        render(
            <MemoryRouter initialEntries={["/customers/1"]}>
                <Routes>
                    <Route path="/customers/:customerId" element={<CustomerDetailPage />} />
                </Routes>
            </MemoryRouter>
        );

        const heading = await screen.findByRole("heading", { name: "John Doe" });
        const customerPanel = heading.closest("section");

        expect(customerPanel).not.toBeNull();
        fireEvent.click(within(customerPanel as HTMLElement).getByRole("button", { name: "Edit" }));

        fireEvent.change(screen.getByLabelText("Name"), { target: { value: "John Smith" } });
        fireEvent.change(screen.getByLabelText("Email"), { target: { value: "john.smith@example.com" } });
	        fireEvent.change(screen.getByLabelText("Phone"), { target: { value: "407-ABC-555-0101" } });
	        expect(screen.getByLabelText("Phone")).toHaveValue("4075550101");
        fireEvent.change(screen.getByLabelText("Type"), { target: { value: "commercial" } });
        fireEvent.change(screen.getByLabelText("Company"), { target: { value: "Smith HVAC" } });
        fireEvent.click(screen.getByRole("button", { name: "Save" }));

        await waitFor(() => {
            expect(mockedUpdateCustomer).toHaveBeenCalledWith(1, {
                name: "John Smith",
                email: "john.smith@example.com",
	                phone: "4075550101",
                customer_type: "commercial",
                company_name: "Smith HVAC",
            });
        });
        expect(await screen.findByRole("heading", { name: "John Smith" })).toBeInTheDocument();
        expect(screen.getByText("john.smith@example.com")).toBeInTheDocument();
    });

    it("opens invoice detail when an invoice row is clicked", async () => {
        render(
            <MemoryRouter initialEntries={["/customers/1"]}>
                <Routes>
                    <Route path="/customers/:customerId" element={<><CustomerDetailPage /><LocationDisplay /></>} />
                    <Route path="/invoices/:invoiceId" element={<LocationDisplay />} />
                </Routes>
            </MemoryRouter>
        );

        fireEvent.click(await screen.findByRole("row", { name: /View invoice 1/i }));

        expect(screen.getByTestId("location-path")).toHaveTextContent("/invoices/1");
    });

    it("opens location detail when a customer location row is clicked", async () => {
        render(
            <MemoryRouter initialEntries={["/customers/1"]}>
                <Routes>
                    <Route path="/customers/:customerId" element={<><CustomerDetailPage /><LocationDisplay /></>} />
                    <Route path="/locations/:locationId" element={<LocationDisplay />} />
                </Routes>
            </MemoryRouter>
        );

        fireEvent.click(await screen.findByRole("row", { name: /View location Home/i }));

        expect(screen.getByTestId("location-path")).toHaveTextContent("/locations/100");
        expect(screen.getByTestId("location-state")).toHaveTextContent("1");
    });

    it("keeps location row actions from opening location detail", async () => {
        render(
            <MemoryRouter initialEntries={["/customers/1"]}>
                <Routes>
                    <Route path="/customers/:customerId" element={<><CustomerDetailPage /><LocationDisplay /></>} />
                    <Route path="/locations/:locationId" element={<LocationDisplay />} />
                </Routes>
            </MemoryRouter>
        );

        const locationRow = await screen.findByRole("row", { name: /View location Home/i });
        fireEvent.click(within(locationRow).getByRole("button", { name: "Edit" }));

        expect(await screen.findByRole("dialog", { name: "Edit Location" })).toBeInTheDocument();
        expect(screen.getByTestId("location-path")).toHaveTextContent("/customers/1");
    });

    it("shows invoice status filters from the invoice history section", async () => {
        render(
            <MemoryRouter initialEntries={["/customers/1"]}>
                <Routes>
                    <Route path="/customers/:customerId" element={<CustomerDetailPage />} />
                </Routes>
            </MemoryRouter>
        );

        const summary = await screen.findByLabelText("Customer invoice summary");
        expect(screen.queryByLabelText("Customer invoice status counts")).not.toBeInTheDocument();

        fireEvent.click(within(summary).getByRole("button", { name: /Invoices/i }));

        expect(await screen.findByRole("button", { name: "All (3)" })).toBeInTheDocument();
        fireEvent.click(within(summary).getByRole("button", { name: /Total Paid/i }));

        expect(screen.getByRole("row", { name: /View invoice 2/i })).toBeInTheDocument();
        expect(screen.queryByRole("row", { name: /View invoice 1/i })).not.toBeInTheDocument();

        fireEvent.click(within(summary).getByRole("button", { name: /Total Owed/i }));

        expect(screen.getByRole("row", { name: /View invoice 1/i })).toBeInTheDocument();
        expect(screen.queryByRole("row", { name: /View invoice 2/i })).not.toBeInTheDocument();
    });

    it("opens an add location dialog from the locations section", async () => {
        render(
            <MemoryRouter initialEntries={["/customers/1"]}>
                <Routes>
                    <Route path="/customers/:customerId" element={<CustomerDetailPage />} />
                </Routes>
            </MemoryRouter>
        );

        fireEvent.click(await screen.findByRole("button", { name: "Add Location" }));

        expect(mockedListLocations).toHaveBeenCalled();
        expect(await screen.findByRole("dialog", { name: "Add Location" })).toBeInTheDocument();
        expect(screen.getByRole("button", { name: "New Address" })).toBeInTheDocument();
        expect(screen.getByRole("button", { name: "Existing Address" })).toBeInTheDocument();
    });

    it("creates a new invoice for the customer and routes to it", async () => {
        render(
            <MemoryRouter initialEntries={["/customers/1"]}>
                <Routes>
                    <Route path="/customers/:customerId" element={<><CustomerDetailPage /><LocationDisplay /></>} />
                    <Route path="/invoices/:invoiceId" element={<LocationDisplay />} />
                </Routes>
            </MemoryRouter>
        );

        fireEvent.click(await screen.findByRole("button", { name: "Create New Invoice" }));

        const dialog = await screen.findByRole("dialog", { name: "Create Invoice" });
        expect(within(dialog).getByLabelText("Customer")).toHaveValue("John Doe - john@example.com");

        fireEvent.change(within(dialog).getByLabelText("Title"), { target: { value: "Mini split install" } });
        fireEvent.change(within(dialog).getByLabelText("Description"), { target: { value: "Installed mini split in upstairs bedroom." } });
        fireEvent.change(within(dialog).getByLabelText("Location"), { target: { value: "10" } });
        fireEvent.change(within(dialog).getByLabelText("Date Issued"), { target: { value: "2026-09-21" } });
        fireEvent.change(within(dialog).getByLabelText("Date Due"), { target: { value: "2026-10-21" } });
        fireEvent.click(within(dialog).getByRole("button", { name: "Create Invoice" }));

        await waitFor(() => {
            expect(screen.getByTestId("location-path")).toHaveTextContent("/invoices/55");
            expect(mockedCreateInvoice).toHaveBeenCalledWith({
                customer_id: 1,
                location_id: 10,
                title: "Mini split install",
                description: "Installed mini split in upstairs bedroom.",
                date_issued: "2026-09-21",
                date_due: "2026-10-21",
            });
        });
    });
});
