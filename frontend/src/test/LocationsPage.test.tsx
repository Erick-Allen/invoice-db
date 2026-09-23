import { fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter, useLocation } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createLocation, listLocations } from "../api/customers";
import { LocationsPage } from "../pages/LocationsPage";

vi.mock("../api/customers", () => ({
    createLocation: vi.fn(),
    listLocations: vi.fn(),
}));

const mockedCreateLocation = vi.mocked(createLocation);
const mockedListLocations = vi.mocked(listLocations);

function LocationDisplay() {
    const location = useLocation();
    return <span data-testid="location-path">{location.pathname}</span>;
}

describe("LocationsPage", () => {
    beforeEach(() => {
        vi.clearAllMocks();

        mockedListLocations.mockResolvedValue([
            {
                id: 3,
                address_line1: "456 Existing Rd",
                address_line2: "Unit 12",
                city: "Tampa",
                state: "FL",
                postal_code: "33602",
                country: "US",
                assigned_customer_count: 1,
                assigned_customer_names: "John Doe",
                assigned_supplier_count: 1,
                assigned_supplier_names: "Johnstone",
                assigned_count: 2,
                assigned_names: "John Doe, Johnstone",
                created_at: "2026-01-01",
                updated_at: "2026-01-01",
            },
        ]);
        mockedCreateLocation.mockResolvedValue({
            id: 4,
            address_line1: "456 Existing Rd",
            address_line2: null,
            city: "Tampa",
            state: "FL",
            postal_code: "33602",
            country: "US",
            assigned_customer_count: 0,
            assigned_customer_names: null,
            assigned_supplier_count: 0,
            assigned_supplier_names: null,
            assigned_count: 0,
            assigned_names: null,
            created_at: "2026-01-01",
            updated_at: "2026-01-01",
        });
    });

    it("renders locations as their own page and opens the create location dialog", async () => {
        render(
            <MemoryRouter>
                <LocationsPage />
            </MemoryRouter>
        );

        expect(screen.getByRole("heading", { name: "Locations" })).toBeInTheDocument();
        expect(await screen.findByText("456 Existing Rd")).toBeInTheDocument();
        expect(screen.getByRole("columnheader", { name: "Unit" })).toBeInTheDocument();
        expect(screen.getByRole("columnheader", { name: "City" })).toBeInTheDocument();
        expect(screen.getByRole("columnheader", { name: "State" })).toBeInTheDocument();
        expect(screen.getByRole("columnheader", { name: "ZIP Code" })).toBeInTheDocument();
        expect(screen.getByRole("columnheader", { name: "Linked To" })).toBeInTheDocument();
        expect(screen.getByText("Unit 12")).toBeInTheDocument();
	        expect(screen.getByText("Tampa")).toBeInTheDocument();
	        expect(screen.getByText("FL")).toBeInTheDocument();
	        expect(screen.getByText("33602")).toBeInTheDocument();
	        expect(screen.getByText("John Doe | Johnstone")).toBeInTheDocument();
	        expect(screen.getByText("Both")).toHaveAttribute("title", "Customer and Supplier");
	        expect(screen.queryByText("Location #3")).not.toBeInTheDocument();

        fireEvent.click(screen.getByRole("button", { name: "Create Location" }));

        const dialog = screen.getByRole("dialog", { name: "Create Location" });
        expect(within(dialog).getByLabelText("Address")).toBeInTheDocument();
        expect(within(dialog).getByLabelText("City")).toBeInTheDocument();
        expect(within(dialog).getByLabelText("State")).toBeInTheDocument();
        expect(within(dialog).getByLabelText("ZIP Code")).toBeInTheDocument();
        expect(within(dialog).getByLabelText("Country")).toBeInTheDocument();
    });

    it("navigates to location detail when a location row is clicked", async () => {
        render(
            <MemoryRouter initialEntries={["/locations"]}>
                <LocationsPage />
                <LocationDisplay />
            </MemoryRouter>
        );

        fireEvent.click(await screen.findByRole("row", { name: /View location 3/i }));

        expect(screen.getByTestId("location-path")).toHaveTextContent("/locations/3");
    });
});
