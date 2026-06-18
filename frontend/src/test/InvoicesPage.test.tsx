import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { listCustomers } from "../api/customers";
import { InvoicesPage } from "../pages/InvoicesPage";
import { listInvoices, updateInvoiceStatus } from "../api/invoices";
import { createPayment, getPaymentSummary, listPayments } from "../api/payments";
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

vi.mock("../api/payments", () => ({
    PAYMENT_METHODS: ["cash", "card", "check", "bank_transfer", "other"],
    listPayments: vi.fn(),
    getPaymentSummary: vi.fn(),
    createPayment: vi.fn(),
    deletePayment: vi.fn(),
}));

const mockedListCustomers = vi.mocked(listCustomers);
const mockedListInvoices = vi.mocked(listInvoices);
const mockedListProducts = vi.mocked(listProducts);
const mockedUpdateInvoiceStatus = vi.mocked(updateInvoiceStatus);
const mockedListPayments = vi.mocked(listPayments);
const mockedGetPaymentSummary = vi.mocked(getPaymentSummary);
const mockedCreatePayment = vi.mocked(createPayment);

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

        mockedListProducts.mockResolvedValue([
            {
                id: 1,
                name: "Widget",
                description: "A test widget",
                unit_price_cents: 1234,
                is_active: true,
            },
        ]);

        mockedGetPaymentSummary.mockResolvedValue({
            invoice_id: 1,
            invoice_total_cents: 2468,
            amount_paid_cents: 500,
            balance_due_cents: 1968,
            is_paid: false,
        });

        mockedListPayments.mockResolvedValue([
            {
                id: 1,
                invoice_id: 1,
                amount_cents: 500,
                payment_date: "2026-06-17",
                method: "cash",
                note: "Initial payment",
            },
        ]);
    });

    it("renders the invoice form and invoice table", async () => {
        render(<InvoicesPage />);

        expect(screen.getByRole("heading", { name: "Invoices"})).toBeInTheDocument();

        expect(screen.getByLabelText("Customer")).toBeInTheDocument();
        expect(screen.getByLabelText("Date Issued")).toBeInTheDocument();
        expect(screen.getByLabelText("Date Due")).toBeInTheDocument();

        expect(screen.getByRole("button", { name : "Create Invoice"})).toBeInTheDocument();

        const johnDoeMatches = await screen.findAllByText(/John Doe/);
        expect(johnDoeMatches.length).toBeGreaterThan(0);
        expect(screen.getAllByText("$24.68").length).toBeGreaterThan(0);
        expect(screen.getByText("Widget x 2")).toBeInTheDocument();
        expect(screen.getAllByText(/Paid \$5.00/).length).toBeGreaterThan(0);
        expect(screen.getByText(/Due \$19.68/)).toBeInTheDocument();
        expect(screen.getByText(/\$5.00 cash on 2026-06-17/)).toBeInTheDocument();
        expect(screen.getByText("draft")).toBeInTheDocument();
        expect(screen.queryByLabelText("Payment amount for invoice 1")).not.toBeInTheDocument();
        
        expect(screen.getByRole("button", { name : "sent"})).toBeInTheDocument();

        expect(screen.getAllByRole("button", {name: "Edit"}).length).toBeGreaterThan(0);
        expect(screen.getAllByRole("button", {name: "Delete"}).length).toBeGreaterThan(0);
    })

    it("shows a retryable error when invoices fail to load", async () => {
        mockedListInvoices.mockRejectedValue(new Error("A database error occurred while retrieving invoices."));

        render(<InvoicesPage />);

        expect(
            await screen.findByText(/Failed to load invoices, line items, and payments/)
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

        render(<InvoicesPage />);

        fireEvent.click(await screen.findByRole("button", { name: "sent" }));

        expect(
            await screen.findByText(/Could not change invoice status/)
        ).toBeInTheDocument();
        expect(
            screen.getByText(/Cannot send invoice with inactive products: Widget/)
        ).toBeInTheDocument();
    });

    it("allows adding a payment for a sent invoice with balance due", async () => {
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
        mockedCreatePayment.mockResolvedValue({
            id: 2,
            invoice_id: 1,
            amount_cents: 1000,
            payment_date: "2026-06-17",
            method: "card",
            note: null,
        });

        render(<InvoicesPage />);

        const amountInput = await screen.findByLabelText("Payment amount for invoice 1");
        fireEvent.change(amountInput, { target: { value: "10.00" } });
        fireEvent.change(screen.getByLabelText("Payment method for invoice 1"), { target: { value: "card" } });
        fireEvent.click(screen.getByRole("button", { name: "Add" }));

        expect(mockedCreatePayment).toHaveBeenCalledWith(1, {
            amount_cents: 1000,
            payment_date: expect.any(String),
            method: "card",
            note: null,
        });
    });

    it("allows paying the remaining balance for a sent invoice", async () => {
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
        mockedCreatePayment.mockResolvedValue({
            id: 2,
            invoice_id: 1,
            amount_cents: 1968,
            payment_date: "2026-06-17",
            method: "check",
            note: "Final payment",
        });

        render(<InvoicesPage />);

        await screen.findByLabelText("Payment amount for invoice 1");
        fireEvent.change(screen.getByLabelText("Payment method for invoice 1"), { target: { value: "check" } });
        fireEvent.change(screen.getByLabelText("Payment note for invoice 1"), { target: { value: "Final payment" } });
        fireEvent.click(screen.getByRole("button", { name: "Pay Balance" }));

        expect(mockedCreatePayment).toHaveBeenCalledWith(1, {
            amount_cents: 1968,
            payment_date: expect.any(String),
            method: "check",
            note: "Final payment",
        });
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

        render(<InvoicesPage />);

        expect(await screen.findByRole("button", { name: "void" })).toBeInTheDocument();
        expect(screen.queryByRole("button", { name: "paid" })).not.toBeInTheDocument();
    });
});
