import { describe, expect, it} from "vitest";
import { centsToDollars, dollarsToCents } from "../utils/money";

describe("money helpers", () => {
    it("converts dollar strings to cents", () => {
        expect(dollarsToCents("100.25")).toBe(10025);
        expect(dollarsToCents("19.9")).toBe(1990);
        expect(dollarsToCents("100")).toBe(10000);
    });

    it("converts cents to dollar display strings", () => {
        expect(centsToDollars(10025)).toBe("100.25");
        expect(centsToDollars(1990)).toBe("19.90")
        expect(centsToDollars(10000)).toBe("100.00")
    });

    it("rejects invalid dollar strings", () => {
        expect(() => dollarsToCents("abc")).toThrow();
        expect(() => dollarsToCents("10.999")).toThrow();
        expect(() => dollarsToCents("")).toThrow();
    });
});