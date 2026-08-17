import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { getReportingOverview } from "../api/reports";
import { ReportingPage } from "../pages/ReportingPage";

vi.mock("../api/reports", () => ({
    getReportingOverview: vi.fn(),
}));

const mockedGetReportingOverview = vi.mocked(getReportingOverview);

describe("ReportingPage", () => {
    beforeEach(() => {
        vi.clearAllMocks();

        mockedGetReportingOverview.mockResolvedValue({
            start_date: null,
            end_date: null,
            summary: {
                invoice_count: 2,
                revenue_total_cents: 8000,
                cost_total_cents: 3000,
                profit_total_cents: 5000,
                outstanding_due_cents: 7000,
            },
            status_breakdown: [
                {
                    status: "draft",
                    invoice_count: 1,
                    revenue_total_cents: 3000,
                },
                {
                    status: "sent",
                    invoice_count: 1,
                    revenue_total_cents: 5000,
                },
            ],
            tag_performance: [
                {
                    tag_id: 1,
                    tag_name: "Commercial",
                    invoice_count: 1,
                    revenue_total_cents: 5000,
                    cost_total_cents: 2000,
                    profit_total_cents: 3000,
                },
            ],
        });
    });

    it("renders reporting summary and performance tables", async () => {
        render(<ReportingPage />);

        expect(screen.getByRole("heading", { name: "Reporting" })).toBeInTheDocument();
        expect(mockedGetReportingOverview).toHaveBeenCalledWith({});

        const summary = await screen.findByLabelText("Reporting performance summary");
        expect(within(summary).getByText("$80.00")).toBeInTheDocument();
        expect(within(summary).getByText("$30.00")).toBeInTheDocument();
        expect(within(summary).getByText("$50.00")).toBeInTheDocument();
        expect(within(summary).getByText("$70.00")).toBeInTheDocument();

        expect(screen.getByText("draft")).toBeInTheDocument();
        expect(screen.getByText("sent")).toBeInTheDocument();
        expect(screen.getByText("Commercial")).toBeInTheDocument();
    });

    it("applies date filters", async () => {
        render(<ReportingPage />);

        await screen.findByLabelText("Reporting performance summary");
        fireEvent.change(screen.getByLabelText("Start Date"), { target: { value: "2026-01-01" } });
        fireEvent.change(screen.getByLabelText("End Date"), { target: { value: "2026-01-31" } });
        fireEvent.click(screen.getByRole("button", { name: "Apply" }));

        await waitFor(() => {
            expect(mockedGetReportingOverview).toHaveBeenLastCalledWith({
                startDate: "2026-01-01",
                endDate: "2026-01-31",
            });
        });
    });

    it("shows an error when report loading fails", async () => {
        mockedGetReportingOverview.mockRejectedValue(new Error("Report failed."));

        render(<ReportingPage />);

        expect(await screen.findByText("Report failed.")).toBeInTheDocument();
    });
});
