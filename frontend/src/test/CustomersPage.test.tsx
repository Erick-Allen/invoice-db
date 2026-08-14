import { fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter, useLocation } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { CustomersPage } from "../pages/CustomersPage";
import { listCustomers } from "../api/customers";

vi.mock("../api/customers", () => ({
    listCustomers: vi.fn(),
    createCustomer: vi.fn(),
    updateCustomer: vi.fn(),
    deleteCustomer: vi.fn(),
}));

const mockedListCustomers = vi.mocked(listCustomers);

function LocationDisplay() {
    const location = useLocation();
    return <span data-testid="location-path">{location.pathname}</span>;
}

describe("CustomersPage", () => {
    beforeEach(() => {
        vi.clearAllMocks();

        mockedListCustomers.mockResolvedValue([
            {
                id: 1,
                name: "John Doe",
                email: "john@example.com",
            },
        ]);
    });

    it("renders the customer form and customer table", async () => {
        render(
            <MemoryRouter>
                <CustomersPage />
            </MemoryRouter>
        );

        expect(screen.getByRole("heading", { name: "Customers" })).toBeInTheDocument();
        expect(screen.queryByRole("dialog", { name: "Create Customer" })).not.toBeInTheDocument();

        expect(screen.getByRole("button", { name: "Create Customer" })).toBeInTheDocument();
        fireEvent.click(screen.getByRole("button", { name: "Create Customer" }));

        const dialog = screen.getByRole("dialog", { name: "Create Customer" });
        expect(within(dialog).getByLabelText("Name")).toBeInTheDocument();
        expect(within(dialog).getByLabelText("Email")).toBeInTheDocument();

        expect(await screen.findByText("John Doe")).toBeInTheDocument();
        expect(screen.getByText("john@example.com")).toBeInTheDocument();

        expect(screen.getByRole("button", { name: "Edit" })).toBeInTheDocument();
        expect(screen.getByRole("button", { name: "Delete" })).toBeInTheDocument();
    });

    it("navigates to customer detail when a customer row is clicked", async () => {
        render(
            <MemoryRouter initialEntries={["/customers"]}>
                <CustomersPage />
                <LocationDisplay />
            </MemoryRouter>
        );

        fireEvent.click(await screen.findByRole("row", { name: /View John Doe/i }));

        expect(screen.getByTestId("location-path")).toHaveTextContent("/customers/1");
    });
});
