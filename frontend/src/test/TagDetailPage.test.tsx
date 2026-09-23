import { fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { getTagDetail } from "../api/tags";
import { TagDetailPage } from "../pages/TagDetailPage";

vi.mock("../api/tags", () => ({
    getTagDetail: vi.fn(),
}));

const mockedGetTagDetail = vi.mocked(getTagDetail);

function LocationDisplay() {
    const location = useLocation();
    return <span data-testid="location-path">{location.pathname}</span>;
}

describe("TagDetailPage", () => {
    beforeEach(() => {
        vi.clearAllMocks();

        mockedGetTagDetail.mockResolvedValue({
            tag: {
                id: 4,
                name: "Install",
                description: "Install work",
                is_active: true,
                created_at: "2026-01-01",
                updated_at: "2026-01-01",
            },
            metrics: {
                invoice_count: 2,
                issued_invoice_count: 1,
                total_invoiced_cents: 5000,
                total_cost_cents: 2000,
                total_paid_cents: 1000,
                net_profit_cents: -1000,
                total_owed_cents: 4000,
            },
            invoices: [
                {
                    id: 7,
                    customer_id: 1,
                    customer_name: "John Doe",
                    location_id: null,
                    date_issued: "2026-09-22",
                    date_due: "2026-10-22",
                    total: 5000,
                    status: "sent",
                    cost_total_cents: 2000,
                    amount_paid_cents: 1000,
                    balance_due_cents: 4000,
                },
            ],
        });
    });

    it("renders tag info, money metrics, and attached invoices", async () => {
        render(
            <MemoryRouter initialEntries={["/tags/4"]}>
                <Routes>
                    <Route path="/tags/:tagId" element={<TagDetailPage />} />
                </Routes>
            </MemoryRouter>
        );

        expect(await screen.findByRole("heading", { name: "Install" })).toBeInTheDocument();
        expect(mockedGetTagDetail).toHaveBeenCalledWith(4);
        expect(screen.getByText("Install work")).toBeInTheDocument();
        expect(screen.getByText("active")).toBeInTheDocument();

        const metrics = screen.getByLabelText("Tag money metrics");
        expect(within(metrics).getByText("Invoices")).toBeInTheDocument();
        expect(within(metrics).getByText("2")).toBeInTheDocument();
        expect(within(metrics).getByText("Issued")).toBeInTheDocument();
        expect(within(metrics).getByText("$50")).toBeInTheDocument();
        expect(within(metrics).getByText("$20")).toBeInTheDocument();
        expect(within(metrics).getByText("$10")).toBeInTheDocument();
        expect(within(metrics).getByText("-$10")).toBeInTheDocument();
        expect(within(metrics).getByText("$40")).toBeInTheDocument();

        const invoiceRow = screen.getByRole("row", { name: /View invoice 7/i });
        expect(within(invoiceRow).getByText("#7")).toBeInTheDocument();
        expect(within(invoiceRow).getByText("John Doe")).toBeInTheDocument();
        expect(within(invoiceRow).getByText("Sep-22-2026")).toBeInTheDocument();
        expect(within(invoiceRow).getByText("sent")).toBeInTheDocument();
    });

    it("links back to the source invoice when opened from invoice detail", async () => {
        render(
            <MemoryRouter initialEntries={[{ pathname: "/tags/4", state: { fromInvoiceId: 7 } }]}>
                <Routes>
                    <Route path="/tags/:tagId" element={<TagDetailPage />} />
                </Routes>
            </MemoryRouter>
        );

        expect(await screen.findByRole("heading", { name: "Install" })).toBeInTheDocument();
        expect(screen.getByRole("link", { name: "Back to invoice" })).toHaveAttribute("href", "/invoices/7");
    });

    it("opens invoice detail when an invoice row is clicked", async () => {
        render(
            <MemoryRouter initialEntries={["/tags/4"]}>
                <Routes>
                    <Route path="/tags/:tagId" element={<><TagDetailPage /><LocationDisplay /></>} />
                    <Route path="/invoices/:invoiceId" element={<LocationDisplay />} />
                </Routes>
            </MemoryRouter>
        );

        fireEvent.click(await screen.findByRole("row", { name: /View invoice 7/i }));

        expect(screen.getByTestId("location-path")).toHaveTextContent("/invoices/7");
    });
});
