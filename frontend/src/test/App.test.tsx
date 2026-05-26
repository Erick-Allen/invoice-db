import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import App from "../App";

describe("App", () => {
    it("renders the app title and navigation", () => {
        render(<App />)

        expect(screen.getByRole("heading" , { name: "Invoice DB" })).toBeInTheDocument();
        expect(screen.getByRole("link" , { name: "Dashboard" })).toBeInTheDocument();
        expect(screen.getByRole("link" , { name: "Customers" })).toBeInTheDocument();
        expect(screen.getByRole("link" , { name: "Invoices" })).toBeInTheDocument();
    })
})