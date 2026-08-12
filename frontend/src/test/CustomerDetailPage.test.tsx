import { fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { getCustomer } from "../api/customers";
import { listInvoices } from "../api/invoices";
import { getPaymentSummary } from "../api/payments";
import { CustomerDetailPage } from "../pages/CustomerDetailPage";

vi.mock("../api/customers", () => ({
    getCustomer: vi.fn(),
}));

vi.mock("../api/invoices", () => ({
    listInvoices: vi.fn(),
}));

vi.mock("../api/payments", () => ({
    getPaymentSummary: vi.fn(),
}));

const mockedGetCustomer = vi.mocked(getCustomer);
const mockedListInvoices = vi.mocked(listInvoices);
const mockedGetPaymentSummary = vi.mocked(getPaymentSummary);

function LocationDisplay() {
    const location = useLocation();
    return <span data-testid="location-path">{location.pathname}</span>;
}

describe("CustomerDetailPage", () => {
    beforeEach(() => {
        vi.clearAllMocks();

        mockedGetCustomer.mockResolvedValue({
            id: 1,
            name: "John Doe",
            email: "john@example.com",
        });
        mockedListInvoices.mockResolvedValue([
            {
                id: 2,
                customer_id: 1,
                date_issued: "2026-06-01",
                date_due: "2026-07-01",
                total: 2500,
                status: "paid",
            },
            {
                id: 1,
                customer_id: 1,
                date_issued: "2026-05-01",
                date_due: "2026-06-01",
                total: 5000,
                status: "sent",
            },
        ]);
        mockedGetPaymentSummary.mockImplementation(async (invoiceId: number) => ({
            invoice_id: invoiceId,
            invoice_total_cents: invoiceId === 1 ? 5000 : 2500,
            amount_paid_cents: invoiceId === 1 ? 1500 : 2500,
            balance_due_cents: invoiceId === 1 ? 3500 : 0,
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
        expect(mockedListInvoices).toHaveBeenCalledWith({ customerId: 1 });
        expect(mockedGetPaymentSummary).toHaveBeenCalledWith(1);
        expect(mockedGetPaymentSummary).toHaveBeenCalledWith(2);

        const summary = screen.getByLabelText("Customer invoice summary");
        expect(within(summary).getByText("Invoices")).toBeInTheDocument();
        expect(within(summary).getByText("2")).toBeInTheDocument();
        expect(within(summary).getByText("$75.00")).toBeInTheDocument();
        expect(within(summary).getByText("$40.00")).toBeInTheDocument();
        expect(within(summary).getByText("$35.00")).toBeInTheDocument();

        const rows = screen.getAllByRole("row");
        expect(within(rows[1]).getByText("#1")).toBeInTheDocument();
        expect(within(rows[2]).getByText("#2")).toBeInTheDocument();
        expect(within(rows[1]).getByText("sent")).toBeInTheDocument();
        expect(within(rows[2]).getByText("paid")).toBeInTheDocument();
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
});
