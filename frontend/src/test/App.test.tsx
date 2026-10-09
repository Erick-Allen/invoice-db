import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import App from "../App";
import { getCurrentUser } from "../api/auth";

vi.mock("../api/auth", () => ({
    continueAsGuest: vi.fn(),
    getCurrentUser: vi.fn(),
    login: vi.fn(),
    logout: vi.fn(),
    signup: vi.fn(),
}));

describe("App", () => {
    beforeEach(() => {
        vi.mocked(getCurrentUser).mockReset();
    });

    it("renders the app title and navigation for an active user", async () => {
        vi.mocked(getCurrentUser).mockResolvedValue({
            isAuthenticated: true,
            isGuest: false,
            workspaceId: 1,
            guestExpiresAt: null,
            user: {
                id: 1,
                email: "user@example.com",
                name: "Test User",
                is_guest: false,
                workspace_id: 1,
                guest_expires_at: null,
            },
        });

        render(<App />)
        expect(await screen.findByRole("heading" , { name: "InvoiceDB" })).toBeInTheDocument();
        expect(screen.getByRole("link", { name: "Dashboard" })).toHaveTextContent("InvoiceDB");
        expect(screen.getAllByRole("link").map((link) => link.textContent)).toEqual([
            "InvoiceDB",
            "Customers",
            "Invoices",
            "Suppliers",
            "Products",
            "Locations",
            "Documents",
            "Reporting",
            "Settings",
        ]);
        expect(screen.getByRole("button", { name: "Sign out" })).toHaveTextContent("Test User · Sign Out");
    })

    it("shows account access when there is no active session", async () => {
        vi.mocked(getCurrentUser).mockRejectedValue(new Error("Signed out"));

        render(<App />);

        expect(await screen.findByRole("heading", { name: "Sign in to save your invoice data." })).toBeInTheDocument();
        expect(screen.getByRole("button", { name: "Continue as Guest" })).toBeInTheDocument();
        expect(screen.queryByRole("heading", { name: "InvoiceDB" })).not.toBeInTheDocument();
    });

    it("shows guest sessions as an exit control", async () => {
        vi.mocked(getCurrentUser).mockResolvedValue({
            isAuthenticated: true,
            isGuest: true,
            workspaceId: 12,
            guestExpiresAt: "2026-10-05T00:00:00+00:00",
            user: {
                id: 42,
                email: null,
                name: "Guest",
                is_guest: true,
                workspace_id: 12,
                guest_expires_at: "2026-10-05T00:00:00+00:00",
            },
        });

        render(<App />);

        expect(await screen.findByRole("button", { name: "Sign out" })).toHaveTextContent("Guest · Sign Out");
    });
})
