import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import App from "../App";

describe("App", () => {
    it("renders the app title and navigation", () => {
        render(<App />)
        expect(screen.getByRole("heading" , { name: "InvoiceDB" })).toBeInTheDocument();
        expect(screen.getAllByRole("link").map((link) => link.textContent)).toEqual([
            "Dashboard",
            "Customers",
            "Invoices",
            "Suppliers",
            "Products",
            "Locations",
            "Reporting",
        ]);
    })
})
