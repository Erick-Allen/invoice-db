import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { getCustomer } from "../api/customers";
import { createInvoiceItem } from "../api/invoiceItems";
import { getInvoice } from "../api/invoices";
import { getPaymentSummary, listPayments } from "../api/payments";
import { listProducts } from "../api/products";
import { addInvoiceTag, listInvoiceTags, listTags, removeInvoiceTag } from "../api/tags";
import { InvoiceDetailPage } from "../pages/InvoiceDetailPage";

vi.mock("../api/customers", () => ({
    getCustomer: vi.fn(),
}));

vi.mock("../api/invoices", () => ({
    getInvoice: vi.fn(),
}));

vi.mock("../api/invoiceItems", () => ({
    createInvoiceItem: vi.fn(),
}));

vi.mock("../api/payments", () => ({
    getPaymentSummary: vi.fn(),
    listPayments: vi.fn(),
}));

vi.mock("../api/products", () => ({
    listProducts: vi.fn(),
}));

vi.mock("../api/tags", () => ({
    addInvoiceTag: vi.fn(),
    listInvoiceTags: vi.fn(),
    listTags: vi.fn(),
    removeInvoiceTag: vi.fn(),
}));

const mockedGetCustomer = vi.mocked(getCustomer);
const mockedCreateInvoiceItem = vi.mocked(createInvoiceItem);
const mockedGetInvoice = vi.mocked(getInvoice);
const mockedGetPaymentSummary = vi.mocked(getPaymentSummary);
const mockedListPayments = vi.mocked(listPayments);
const mockedListProducts = vi.mocked(listProducts);
const mockedAddInvoiceTag = vi.mocked(addInvoiceTag);
const mockedListInvoiceTags = vi.mocked(listInvoiceTags);
const mockedListTags = vi.mocked(listTags);
const mockedRemoveInvoiceTag = vi.mocked(removeInvoiceTag);

describe("InvoiceDetailPage", () => {
    beforeEach(() => {
        vi.clearAllMocks();

        mockedGetInvoice.mockResolvedValue({
            id: 7,
            customer_id: 1,
            date_issued: "2026-06-01",
            date_due: "2026-07-01",
            total: 7500,
            status: "sent",
            items: [
                {
                    id: 11,
                    invoice_id: 7,
                    product_id: 3,
                    quantity: 2,
                    unit_price_cents: 2500,
                    line_total_cents: 5000,
                },
            ],
        });
        mockedGetCustomer.mockResolvedValue({
            id: 1,
            name: "John Doe",
            email: "john@example.com",
        });
        mockedGetPaymentSummary.mockResolvedValue({
            invoice_id: 7,
            invoice_total_cents: 7500,
            amount_paid_cents: 2500,
            balance_due_cents: 5000,
            is_paid: false,
        });
        mockedListPayments.mockResolvedValue([
            {
                id: 9,
                invoice_id: 7,
                amount_cents: 2500,
                payment_date: "2026-06-15",
                method: "card",
                note: "Deposit",
            },
        ]);
        mockedListProducts.mockResolvedValue([
            {
                id: 3,
                name: "Consulting",
                description: null,
                cost_cents: 0,
                unit_price_cents: 2500,
                category_id: 2,
                category_name: "Labor",
                is_active: true,
            },
            {
                id: 4,
                name: "Hosting",
                description: null,
                cost_cents: 0,
                unit_price_cents: 1500,
                category_id: 3,
                category_name: "Infrastructure",
                is_active: true,
            },
        ]);
        mockedListTags.mockResolvedValue([
            {
                id: 1,
                name: "Commercial",
                description: null,
                is_active: true,
            },
        ]);
        mockedListInvoiceTags.mockResolvedValue([
            {
                id: 2,
                name: "Repair",
                description: null,
                is_active: true,
            },
        ]);
        mockedAddInvoiceTag.mockResolvedValue({
            invoice_id: 7,
            tag_id: 1,
            created_at: "2026-08-17T00:00:00",
        });
        mockedRemoveInvoiceTag.mockResolvedValue(undefined);
        mockedCreateInvoiceItem.mockResolvedValue({
            id: 12,
            invoice_id: 7,
            product_id: 4,
            quantity: 3,
            unit_price_cents: 1500,
            line_total_cents: 4500,
        });
    });

    it("renders invoice detail with line items and payments", async () => {
        render(
            <MemoryRouter initialEntries={["/invoices/7"]}>
                <Routes>
                    <Route path="/invoices/:invoiceId" element={<InvoiceDetailPage />} />
                </Routes>
            </MemoryRouter>
        );

        expect(await screen.findByRole("heading", { name: "Invoice #7", level: 2 })).toBeInTheDocument();
        expect(mockedGetInvoice).toHaveBeenCalledWith(7, true);
        expect(mockedGetCustomer).toHaveBeenCalledWith(1);
        expect(mockedListPayments).toHaveBeenCalledWith(7);
        expect(mockedGetPaymentSummary).toHaveBeenCalledWith(7);
        expect(mockedListTags).toHaveBeenCalledWith(true);
        expect(mockedListInvoiceTags).toHaveBeenCalledWith(7);

        const summary = screen.getByLabelText("Invoice payment summary");
        expect(within(summary).getByText("$75.00")).toBeInTheDocument();
        expect(within(summary).getByText("$25.00")).toBeInTheDocument();
        expect(within(summary).getByText("$50.00")).toBeInTheDocument();

        expect(screen.getAllByText("John Doe").length).toBeGreaterThan(0);
        expect(screen.getAllByText("Consulting").length).toBeGreaterThan(0);
        expect(screen.getAllByText("Labor").length).toBeGreaterThan(0);
        expect(screen.getByText("Repair")).toBeInTheDocument();
        expect(screen.getByText("Deposit")).toBeInTheDocument();
        expect(screen.getByRole("link", { name: "Back to invoices" })).toHaveAttribute("href", "/invoices");
    });

    it("links back to the source customer when opened from customer detail", async () => {
        render(
            <MemoryRouter initialEntries={[{ pathname: "/invoices/7", state: { fromCustomerId: 1 } }]}>
                <Routes>
                    <Route path="/invoices/:invoiceId" element={<InvoiceDetailPage />} />
                </Routes>
            </MemoryRouter>
        );

        expect(await screen.findByRole("heading", { name: "Invoice #7", level: 2 })).toBeInTheDocument();
        expect(screen.getByRole("link", { name: "Back to customer" })).toHaveAttribute("href", "/customers/1");
    });

    it("renders a customer-facing print invoice layout", async () => {
        render(
            <MemoryRouter initialEntries={["/invoices/7"]}>
                <Routes>
                    <Route path="/invoices/:invoiceId" element={<InvoiceDetailPage />} />
                </Routes>
            </MemoryRouter>
        );

        const printableInvoice = await screen.findByLabelText("Printable customer invoice");

        expect(within(printableInvoice).getByRole("heading", { name: "Invoice #7" })).toBeInTheDocument();
        expect(within(printableInvoice).getByText("Bill To")).toBeInTheDocument();
        expect(within(printableInvoice).getByText("John Doe")).toBeInTheDocument();
        expect(within(printableInvoice).getByText("Balance Due")).toBeInTheDocument();
        expect(within(printableInvoice).queryByText("Payments")).not.toBeInTheDocument();
    });

    it("prints the invoice detail", async () => {
        const printSpy = vi.spyOn(window, "print").mockImplementation(() => undefined);

        render(
            <MemoryRouter initialEntries={["/invoices/7"]}>
                <Routes>
                    <Route path="/invoices/:invoiceId" element={<InvoiceDetailPage />} />
                </Routes>
            </MemoryRouter>
        );

        fireEvent.click(await screen.findByRole("button", { name: "Print" }));

        expect(printSpy).toHaveBeenCalledOnce();
        printSpy.mockRestore();
    });

    it("adds a line item to a draft invoice from detail", async () => {
        mockedGetInvoice.mockResolvedValue({
            id: 7,
            customer_id: 1,
            date_issued: "2026-06-01",
            date_due: "2026-07-01",
            total: 0,
            status: "draft",
            items: [],
        });

        render(
            <MemoryRouter initialEntries={["/invoices/7"]}>
                <Routes>
                    <Route path="/invoices/:invoiceId" element={<InvoiceDetailPage />} />
                </Routes>
            </MemoryRouter>
        );

        await screen.findByRole("heading", { name: "Invoice #7", level: 2 });
        fireEvent.change(screen.getByLabelText("Product for new invoice detail item"), { target: { value: "4" } });
        fireEvent.change(screen.getByLabelText("Quantity for new invoice detail item"), { target: { value: "3" } });
        fireEvent.click(screen.getByRole("button", { name: "Add Item" }));

        await waitFor(() => {
            expect(mockedCreateInvoiceItem).toHaveBeenCalledWith(7, {
                product_id: 4,
                quantity: 3,
                unit_price_cents: null,
            });
        });
    });

    it("adds and removes invoice tags from detail", async () => {
        render(
            <MemoryRouter initialEntries={["/invoices/7"]}>
                <Routes>
                    <Route path="/invoices/:invoiceId" element={<InvoiceDetailPage />} />
                </Routes>
            </MemoryRouter>
        );

        await screen.findByRole("heading", { name: "Invoice #7", level: 2 });
        fireEvent.change(screen.getByLabelText("Tag for invoice"), { target: { value: "1" } });
        fireEvent.click(screen.getByRole("button", { name: "Add Tag" }));

        await waitFor(() => {
            expect(mockedAddInvoiceTag).toHaveBeenCalledWith(7, { tag_id: 1 });
        });

        fireEvent.click(screen.getByRole("button", { name: "Remove Repair tag" }));

        await waitFor(() => {
            expect(mockedRemoveInvoiceTag).toHaveBeenCalledWith(7, 2);
        });
    });
});
