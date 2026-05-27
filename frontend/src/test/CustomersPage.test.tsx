import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi} from "vitest";
import { CustomersPage } from "../pages/CustomersPage";
import { listCustomers } from "../api/customers";

vi.mock("../api/customers", () => ({
    listCustomers: vi.fn(),
    createCustomer: vi.fn(),
    updateCustomer: vi.fn(),
    deleteCustomer: vi.fn(),
}));

const mockedListCustomers = vi.mocked(listCustomers);

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
        render(<CustomersPage />);

        expect(screen.getByRole("heading", {name: "Customers"})).toBeInTheDocument();

        expect(screen.getByLabelText("Name")).toBeInTheDocument();
        expect(screen.getByLabelText("Email")).toBeInTheDocument();
        expect(screen.getByRole("button", {name: "Create Customer"})).toBeInTheDocument();

        expect(await screen.findByText("John Doe")).toBeInTheDocument();
        expect(screen.getByText("john@example.com")).toBeInTheDocument();

        expect(screen.getByRole("button", {name: "Edit"})).toBeInTheDocument();
        expect(screen.getByRole("button", {name: "Delete"})).toBeInTheDocument();
    });
})