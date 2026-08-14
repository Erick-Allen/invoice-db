import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter, useLocation } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { listCustomers } from "../api/customers";
import { InvoicesPage } from "../pages/InvoicesPage";
import { createInvoice, listInvoices, updateInvoiceStatus } from "../api/invoices";
import { createInvoiceItem } from "../api/invoiceItems";
import { listProducts } from "../api/products";

vi.mock("../api/customers", () => ({
    listCustomers: vi.fn(),
}));

vi.mock("../api/invoices", () => ({
    listInvoices: vi.fn(),
    createInvoice: vi.fn(),
    updateInvoice: vi.fn(),
    updateInvoiceStatus: vi.fn(),
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

const mockedListCustomers = vi.mocked(listCustomers);
const mockedCreateInvoice = vi.mocked(createInvoice);
const mockedListInvoices = vi.mocked(listInvoices);
const mockedCreateInvoiceItem = vi.mocked(createInvoiceItem);
const mockedListProducts = vi.mocked(listProducts);
const mockedUpdateInvoiceStatus = vi.mocked(updateInvoiceStatus);

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
                        unit_price_cents: 1234,
                        line_total_cents: 2468,
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
            unit_price_cents: 1234,
            line_total_cents: 2468,
        });

        mockedListProducts.mockResolvedValue([
            {
                id: 1,
                name: "Widget",
                description: "A test widget",
                unit_price_cents: 1234,
                category_id: 1,
                category_name: "Uncategorized",
                is_active: true,
            },
        ]);

    });

    it("renders the invoice form and invoice table", async () => {
        renderInvoicesPage();

        expect(screen.getByRole("heading", { name: "Invoices"})).toBeInTheDocument();

        expect(screen.getByRole("button", { name : "Create Invoice"})).toBeInTheDocument();
        expect(screen.queryByRole("dialog", { name: "Create Invoice" })).not.toBeInTheDocument();
        fireEvent.click(screen.getByRole("button", { name : "Create Invoice"}));

        const dialog = screen.getByRole("dialog", { name: "Create Invoice" });
        expect(within(dialog).getByLabelText("Customer")).toBeInTheDocument();
        expect(within(dialog).getByLabelText("Date Issued")).toBeInTheDocument();
        expect(within(dialog).getByLabelText("Date Due")).toBeInTheDocument();
        expect(within(dialog).getByLabelText("Product for new invoice item 1")).toBeInTheDocument();

        const johnDoeMatches = await screen.findAllByText(/John Doe/);
        expect(johnDoeMatches.length).toBeGreaterThan(0);
        expect(screen.getAllByText("$24.68").length).toBeGreaterThan(0);
        expect(screen.getByText("1 item")).toBeInTheDocument();
        expect(screen.getByText("draft")).toBeInTheDocument();
        expect(screen.queryByLabelText("Payment amount for invoice 1")).not.toBeInTheDocument();
        
        expect(screen.getByRole("button", { name : "sent"})).toBeInTheDocument();

        expect(screen.getAllByRole("button", {name: "Edit"}).length).toBeGreaterThan(0);
        expect(screen.getAllByRole("button", {name: "Delete"}).length).toBeGreaterThan(0);
    })

    it("creates an invoice with selected line items", async () => {
        renderInvoicesPage();

        expect(await screen.findByText("John Doe")).toBeInTheDocument();
        fireEvent.click(screen.getByRole("button", { name: "Create Invoice" }));
        const dialog = screen.getByRole("dialog", { name: "Create Invoice" });

        fireEvent.change(within(dialog).getByLabelText("Customer"), { target: { value: "1" } });
        fireEvent.change(within(dialog).getByLabelText("Date Issued"), { target: { value: "2026-06-01" } });
        fireEvent.change(within(dialog).getByLabelText("Date Due"), { target: { value: "2026-07-01" } });
        fireEvent.change(within(dialog).getByLabelText("Product for new invoice item 1"), { target: { value: "1" } });
        fireEvent.change(within(dialog).getByLabelText("Quantity for new invoice item 1"), { target: { value: "2" } });
        await waitFor(() => {
            expect(within(dialog).getByLabelText("Customer")).toHaveValue("1");
        });
        fireEvent.click(within(dialog).getByRole("button", { name: "Create Invoice" }));

        await waitFor(() => {
            expect(mockedCreateInvoice).toHaveBeenCalledWith({
                customer_id: 1,
                date_issued: "2026-06-01",
                date_due: "2026-07-01",
            });
        });
        await waitFor(() => {
            expect(mockedCreateInvoiceItem).toHaveBeenCalledWith(2, {
                product_id: 1,
                quantity: 2,
                unit_price_cents: null,
            });
        });
    });

    it("opens invoice detail when an invoice row is clicked", async () => {
        renderInvoicesPage();

        fireEvent.click(await screen.findByRole("row", { name: /View invoice 1/i }));

        expect(screen.getByTestId("location-path")).toHaveTextContent("/invoices/1");
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

    it("shows the backend message when a status change fails", async () => {
        mockedUpdateInvoiceStatus.mockRejectedValue(
            new Error("Cannot send invoice with inactive products: Widget.")
        );

        renderInvoicesPage();

        fireEvent.click(await screen.findByRole("button", { name: "sent" }));

        expect(
            await screen.findByText(/Could not change invoice status/)
        ).toBeInTheDocument();
        expect(
            screen.getByText(/Cannot send invoice with inactive products: Widget/)
        ).toBeInTheDocument();
    });

    it("only offers void as a manual status change for sent invoices", async () => {
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

        expect(await screen.findByRole("button", { name: "void" })).toBeInTheDocument();
        expect(screen.queryByRole("button", { name: "paid" })).not.toBeInTheDocument();
    });
});
