import { describe, expect, it } from "vitest";
import { formatDisplayDate, getDefaultSentInvoiceDueDate, getDefaultSentInvoiceIssuedDate } from "../utils/date";

describe("formatDisplayDate", () => {
    it("formats stored invoice dates for display", () => {
        expect(formatDisplayDate("2026-01-05")).toBe("Jan-5-2026");
        expect(formatDisplayDate("2026-09-23")).toBe("Sep-23-2026");
    });

    it("falls back for empty or unexpected values", () => {
        expect(formatDisplayDate(null)).toBe("-");
        expect(formatDisplayDate(undefined)).toBe("-");
        expect(formatDisplayDate("not-a-date")).toBe("not-a-date");
    });

    it("calculates the default sent invoice due date", () => {
        expect(getDefaultSentInvoiceDueDate(new Date("2026-09-22T12:00:00"))).toBe("2026-10-22");
    });

    it("calculates the default sent invoice issued date", () => {
        expect(getDefaultSentInvoiceIssuedDate(new Date("2026-09-22T12:00:00"))).toBe("2026-09-22");
    });
});
