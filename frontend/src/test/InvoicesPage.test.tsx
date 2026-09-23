import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter, useLocation } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { listCustomerLocations, listCustomers } from "../api/customers";
import { InvoicesPage } from "../pages/InvoicesPage";
import { createInvoice, listInvoices } from "../api/invoices";
import { createInvoiceItem } from "../api/invoiceItems";
import { listProducts } from "../api/products";
import { listTags } from "../api/tags";

vi.mock("../api/customers", () => ({
    listCustomers: vi.fn(),
    listCustomerLocations: vi.fn(),
}));

vi.mock("../api/invoices", () => ({
    listInvoices: vi.fn(),
    createInvoice: vi.fn(),
    deleteInvoice: vi.fn(),
}));

vi.mock("../api/products", () => ({
    listProducts: vi.fn(),
}));

vi.mock("../api/invoiceItems", () => ({
    createInvoiceItem: vi.fn(),
    updateInvoiceItem: vi.fn(),
    deleteInvoiceItem: vi.fn(),
}));

vi.mock("../api/tags", () => ({
    createTag: vi.fn(),
    deactivateTag: vi.fn(),
    deleteTag: vi.fn(),
    listTags: vi.fn(),
    updateTag: vi.fn(),
}));

const mockedListCustomers = vi.mocked(listCustomers);
const mockedListCustomerLocations = vi.mocked(listCustomerLocations);
const mockedCreateInvoice = vi.mocked(createInvoice);
const mockedListInvoices = vi.mocked(listInvoices);
const mockedCreateInvoiceItem = vi.mocked(createInvoiceItem);
const mockedListProducts = vi.mocked(listProducts);
const mockedListTags = vi.mocked(listTags);

function LocationDisplay() {
    const location = useLocation();
    return <span data-testid="location-path">{location.pathname}</span>;
}

function renderInvoicesPage() {
    return render(
        <MemoryRouter initialEntries={["/invoices"]}>
            <InvoicesPage />
            <LocationDisplay />
        </MemoryRouter>
    );
}

describe("InvoicesPage", () => {
    beforeEach(() => {
        vi.clearAllMocks();

        mockedListCustomers.mockResolvedValue([
            {
                id: 1,
                name: "John Doe",
                email: "john@example.com",
            },
        ]);
        mockedListCustomerLocations.mockResolvedValue([]);

        mockedListInvoices.mockResolvedValue([
            {
                id: 1,
                customer_id: 1,
                date_issued: "2026-05-20",
                date_due: "2026-06-20",
                total: 2468,
                status: "draft",
                items: [
                    {
                        id: 1,
                        invoice_id: 1,
                        product_id: 1,
                        quantity: 2,
                        unit_cost_cents: 900,
                        cost_total_cents: 1800,
                        unit_price_cents: 1234,
                        line_total_cents: 2468,
                        profit_total_cents: 668,
                    },
                ],
            },
        ])
        mockedCreateInvoice.mockResolvedValue({
            id: 2,
            customer_id: 1,
            date_issued: "2026-06-01",
            date_due: "2026-07-01",
            total: 0,
            status: "draft",
            items: [],
        });
        mockedCreateInvoiceItem.mockResolvedValue({
            id: 3,
            invoice_id: 2,
            product_id: 1,
            quantity: 2,
            unit_cost_cents: 900,
            cost_total_cents: 1800,
            unit_price_cents: 1234,
            line_total_cents: 2468,
            profit_total_cents: 668,
        });

        mockedListProducts.mockResolvedValue([
            {
                id: 1,
                name: "Widget",
                description: "A test widget",
                cost_cents: 900,
                unit_price_cents: 1234,
                category_id: 1,
                category_name: "Uncategorized",
                is_active: true,
            },
            {
                id: 2,
                name: "Free inspection",
                description: null,
                cost_cents: 0,
                unit_price_cents: 0,
                category_id: 1,
                category_name: "Uncategorized",
                is_active: true,
            },
        ]);
        mockedListTags.mockResolvedValue([]);

    });

    it("renders the invoice form and invoice table", async () => {
        renderInvoicesPage();

        expect(screen.getByRole("heading", { name: "Invoices"})).toBeInTheDocument();

        expect(screen.getByRole("button", { name : "Create Invoice"})).toBeInTheDocument();
        expect(screen.queryByRole("dialog", { name: "Create Invoice" })).not.toBeInTheDocument();
        fireEvent.click(screen.getByRole("button", { name : "Create Invoice"}));

        const dialog = screen.getByRole("dialog", { name: "Create Invoice" });
        expect(within(dialog).getByLabelText("Customer")).toBeInTheDocument();
        expect(within(dialog).queryByLabelText("Date Issued")).not.toBeInTheDocument();
        expect(within(dialog).queryByLabelText("Due Date")).not.toBeInTheDocument();
        expect(within(dialog).getByLabelText("Product for new invoice item 1")).toBeInTheDocument();
        expect(within(dialog).getByLabelText("Quantity for new invoice item 1")).toBeDisabled();
        expect(within(dialog).getByLabelText("Unit cost for new invoice item 1")).toBeDisabled();
        expect(within(dialog).getByLabelText("Unit price for new invoice item 1")).toBeDisabled();
        expect(within(dialog).getByLabelText("Unit cost for new invoice item 1")).toHaveAttribute("placeholder", "0");
        expect(within(dialog).getByLabelText("Unit price for new invoice item 1")).toHaveAttribute("placeholder", "0");
        expect(await within(dialog).findByRole("option", { name: "Free inspection - $0" })).toBeInTheDocument();
        expect(within(dialog).getByRole("option", { name: "Widget - $12.34" })).toBeInTheDocument();

        const johnDoeMatches = await screen.findAllByText(/John Doe/);
        expect(johnDoeMatches.length).toBeGreaterThan(0);
        expect(screen.getAllByText("$24.68").length).toBeGreaterThan(0);
        expect(screen.getAllByText("1 item").length).toBeGreaterThan(0);
	        expect(screen.getByText("draft")).toBeInTheDocument();
	        expect(screen.getByRole("columnheader", { name: "#" })).toBeInTheDocument();
	        expect(screen.getByRole("cell", { name: "1" })).toBeInTheDocument();
	        expect(screen.queryByRole("columnheader", { name: "Title" })).not.toBeInTheDocument();
	        expect(screen.queryByRole("columnheader", { name: "Line Items" })).not.toBeInTheDocument();
	        expect(screen.queryByRole("columnheader", { name: "Date Issued" })).not.toBeInTheDocument();
	        expect(screen.getByRole("columnheader", { name: "Date Due" })).toBeInTheDocument();
	        expect(screen.queryByLabelText("Payment amount for invoice 1")).not.toBeInTheDocument();
        expect(screen.queryByRole("button", { name : "sent"})).not.toBeInTheDocument();

	        expect(screen.queryByRole("button", {name: "Edit"})).not.toBeInTheDocument();
	        expect(screen.getAllByRole("button", {name: "Delete"}).length).toBeGreaterThan(0);
	        const invoiceTable = screen.getByRole("table");
	        const assistantHeading = screen.getByRole("heading", { name: "Invoice Assistant" });
	        expect(invoiceTable.compareDocumentPosition(assistantHeading) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
	    })

    it("shows invoice location options with their address", async () => {
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
            {
                id: 11,
                customer_id: 1,
                location_id: 101,
                label: "Shop",
                address_line1: "456 Service Rd",
                address_line2: null,
                city: "Orlando",
                state: "FL",
                postal_code: "32802",
                country: "US",
                is_primary: false,
                is_active: true,
                notes: null,
                created_at: "2026-01-01",
                updated_at: "2026-01-01",
            },
        ]);

        renderInvoicesPage();

        expect(await screen.findByText("John Doe")).toBeInTheDocument();
        fireEvent.click(screen.getByRole("button", { name: "Create Invoice" }));
        const dialog = screen.getByRole("dialog", { name: "Create Invoice" });

        fireEvent.change(within(dialog).getByLabelText("Customer"), { target: { value: "1" } });

        expect(
            within(dialog).getByRole("option", { name: "123 Main St, Orlando, FL 32801" })
        ).toBeInTheDocument();
        expect(
            within(dialog).getByRole("option", { name: "456 Service Rd, Orlando, FL 32802" })
        ).toBeInTheDocument();
        expect(within(dialog).queryByRole("option", { name: /Home/ })).not.toBeInTheDocument();
        expect(within(dialog).queryByRole("option", { name: /Shop/ })).not.toBeInTheDocument();
    });

    it("creates an invoice with selected line items", async () => {
        renderInvoicesPage();

        expect(await screen.findByText("John Doe")).toBeInTheDocument();
        fireEvent.click(screen.getByRole("button", { name: "Create Invoice" }));
        const dialog = screen.getByRole("dialog", { name: "Create Invoice" });

        fireEvent.change(within(dialog).getByLabelText("Customer"), { target: { value: "1" } });
        fireEvent.change(within(dialog).getByLabelText("Product for new invoice item 1"), { target: { value: "2" } });
        expect(within(dialog).getByLabelText("Unit cost for new invoice item 1")).toHaveValue("0");
        expect(within(dialog).getByLabelText("Unit price for new invoice item 1")).toHaveValue("0");
        fireEvent.change(within(dialog).getByLabelText("Product for new invoice item 1"), { target: { value: "1" } });
        expect(within(dialog).getByLabelText("Quantity for new invoice item 1")).toBeEnabled();
        expect(within(dialog).getByLabelText("Unit cost for new invoice item 1")).toBeEnabled();
        expect(within(dialog).getByLabelText("Unit price for new invoice item 1")).toBeEnabled();
        expect(within(dialog).getByLabelText("Unit cost for new invoice item 1")).toHaveValue("9");
        expect(within(dialog).getByLabelText("Unit price for new invoice item 1")).toHaveValue("12.34");
        fireEvent.click(within(dialog).getByRole("button", { name: "Add Item" }));
        const firstProductSelect = within(dialog).getByLabelText("Product for new invoice item 1");
        const secondProductSelect = within(dialog).getByLabelText("Product for new invoice item 2");
        expect(within(firstProductSelect).getByRole("option", { name: "Widget - $12.34" })).toBeInTheDocument();
        expect(within(secondProductSelect).queryByRole("option", { name: "Widget - $12.34" })).not.toBeInTheDocument();
        expect(within(secondProductSelect).getByRole("option", { name: "Free inspection - $0" })).toBeInTheDocument();
        fireEvent.change(within(dialog).getByLabelText("Quantity for new invoice item 1"), { target: { value: "2" } });
        fireEvent.change(within(dialog).getByLabelText("Unit cost for new invoice item 1"), { target: { value: "9" } });
        await waitFor(() => {
            expect(within(dialog).getByLabelText("Customer")).toHaveValue("1");
        });
        expect(within(dialog).getByLabelText("Title")).toHaveValue("");
        expect(within(dialog).getByLabelText("Description")).toHaveValue("");
        fireEvent.click(within(dialog).getByRole("button", { name: "Create Invoice" }));

        await waitFor(() => {
            expect(mockedCreateInvoice).toHaveBeenCalledWith({
                customer_id: 1,
                location_id: null,
                title: null,
                description: null,
                date_issued: null,
                date_due: null,
            });
        });
        await waitFor(() => {
            expect(mockedCreateInvoiceItem).toHaveBeenCalledWith(2, {
                product_id: 1,
                quantity: 2,
                unit_cost_cents: 900,
                unit_price_cents: 1234,
            });
        });
    });

    it("opens invoice detail when an invoice row is clicked", async () => {
        renderInvoicesPage();

        fireEvent.click(await screen.findByRole("row", { name: /View invoice 1/i }));

        expect(screen.getByTestId("location-path")).toHaveTextContent("/invoices/1");
    });

    it("opens tag detail when a tag row is clicked", async () => {
        mockedListTags.mockResolvedValue([
            {
                id: 2,
                name: "Repair",
                description: "Repair work",
                is_active: true,
            },
        ]);

        renderInvoicesPage();

        fireEvent.click(screen.getByRole("button", { name: "Tags" }));
        fireEvent.click(await screen.findByRole("row", { name: /View tag Repair/i }));

        expect(screen.getByTestId("location-path")).toHaveTextContent("/tags/2");
    });

    it("shows a retryable error when invoices fail to load", async () => {
        mockedListInvoices.mockRejectedValue(new Error("A database error occurred while retrieving invoices."));

        renderInvoicesPage();

        expect(
            await screen.findByText(/Failed to load invoices and line items/)
        ).toBeInTheDocument();
        expect(
            screen.getByText(/A database error occurred while retrieving invoices/)
        ).toBeInTheDocument();
        expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
        expect(screen.queryByText("No invoices found.")).not.toBeInTheDocument();
    });

    it("does not offer manual status changes from the invoice list", async () => {
        mockedListInvoices.mockResolvedValue([
            {
                id: 1,
                customer_id: 1,
                date_issued: "2026-05-20",
                date_due: "2026-06-20",
                total: 2468,
                status: "sent",
                items: [],
            },
        ]);

        renderInvoicesPage();

        expect(await screen.findByText("sent")).toBeInTheDocument();
        expect(screen.queryByRole("button", { name: "void" })).not.toBeInTheDocument();
        expect(screen.queryByRole("button", { name: "paid" })).not.toBeInTheDocument();
    });
});
