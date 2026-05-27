import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { listCustomers } from "../api/customers";
import { InvoicesPage } from "../pages/InvoicesPage";
import { listInvoices } from "../api/invoices";

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

const mockedListCustomers = vi.mocked(listCustomers);
const mockedListInvoices = vi.mocked(listInvoices);

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
                total: 10025,
                status: "draft",
            },
        ])
    });

    it("renders the invoice form and invoice table", async () => {
        render(<InvoicesPage />);

        expect(screen.getByRole("heading", { name: "Invoices"})).toBeInTheDocument();

        expect(screen.getByLabelText("Customer")).toBeInTheDocument();
        expect(screen.getByLabelText("Date Issued")).toBeInTheDocument();
        expect(screen.getByLabelText("Date Due")).toBeInTheDocument();
        expect(screen.getByLabelText("Total")).toBeInTheDocument();

        expect(screen.getByRole("button", { name : "Create Invoice"})).toBeInTheDocument();

        const johnDoeMatches = await screen.findAllByText(/John Doe/);
        expect(johnDoeMatches.length).toBeGreaterThan(0);
        expect(screen.getByText("$100.25")).toBeInTheDocument();
        expect(screen.getByText("draft")).toBeInTheDocument();
        
        expect(screen.getByRole("button", { name : "sent"})).toBeInTheDocument();

        expect(screen.getByRole("button", {name: "Edit"})).toBeInTheDocument();
        expect(screen.getByRole("button", {name: "Delete"})).toBeInTheDocument();
    })
});
