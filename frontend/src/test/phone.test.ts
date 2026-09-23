import { describe, expect, it } from "vitest";
import { digitsOnly, formatPhoneNumber, isValidCustomerPhone } from "../utils/phone";

describe("phone utilities", () => {
    it("keeps only digits", () => {
        expect(digitsOnly("407-ABC-555-0100")).toBe("4075550100");
    });

    it("validates and formats 10-digit phone numbers", () => {
        expect(isValidCustomerPhone("")).toBe(true);
        expect(isValidCustomerPhone("5550100")).toBe(false);
        expect(isValidCustomerPhone("4075550100")).toBe(true);
        expect(formatPhoneNumber("5550100")).toBe("5550100");
        expect(formatPhoneNumber("4075550100")).toBe("(407) 555-0100");
    });
});
