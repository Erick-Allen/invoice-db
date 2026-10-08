import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { getBusinessProfile, saveBusinessProfile, type BusinessProfile } from "../api/businessProfile";
import { BusinessProfilePage } from "../pages/BusinessProfilePage";

vi.mock("../api/businessProfile", () => ({
    getBusinessProfile: vi.fn(),
    saveBusinessProfile: vi.fn(),
}));

const emptyProfile: BusinessProfile = {
    id: null,
    workspace_id: 1,
    business_name: null,
    email: null,
    phone: null,
    website: null,
    address_line1: null,
    address_line2: null,
    city: null,
    state: null,
    postal_code: null,
    default_payment_terms_days: null,
    ways_to_pay: null,
    default_tax_rate: null,
    default_invoice_footer: null,
    logo_url: null,
    created_at: null,
    updated_at: null,
};

describe("BusinessProfilePage", () => {
    beforeEach(() => {
        vi.mocked(getBusinessProfile).mockReset();
        vi.mocked(saveBusinessProfile).mockReset();
        vi.mocked(getBusinessProfile).mockResolvedValue(emptyProfile);
        vi.mocked(saveBusinessProfile).mockImplementation(async (payload) => ({
            ...emptyProfile,
            id: 1,
            business_name: payload.business_name ?? null,
            email: payload.email ?? null,
            phone: payload.phone ?? null,
            website: payload.website ?? null,
            address_line1: payload.address_line1 ?? null,
            address_line2: payload.address_line2 ?? null,
            city: payload.city ?? null,
            state: payload.state ?? null,
            postal_code: payload.postal_code ?? null,
            default_payment_terms_days: payload.default_payment_terms_days ?? null,
            ways_to_pay: payload.ways_to_pay ?? null,
            default_tax_rate: payload.default_tax_rate ?? null,
            default_invoice_footer: payload.default_invoice_footer ?? null,
            logo_url: payload.logo_url ?? null,
        }));
    });

    it("renders business profile fields and invoice sender preview", async () => {
        const user = userEvent.setup();

        render(<BusinessProfilePage />);

        expect(screen.getByRole("heading", { name: "Settings" })).toBeInTheDocument();
        expect(await screen.findByRole("button", { name: "Edit Settings" })).toBeEnabled();
        expect(screen.queryByRole("form", { name: "Business profile form" })).not.toBeInTheDocument();

        await user.click(screen.getByRole("button", { name: "Edit Settings" }));

        expect(screen.getByRole("form", { name: "Business profile form" })).toBeInTheDocument();
        expect(await screen.findByRole("button", { name: "Save Settings" })).toBeEnabled();

        await user.type(screen.getByLabelText("Business Name"), "Allen Studio");
        await user.type(screen.getByLabelText("Email"), "billing@example.com");
        await user.type(screen.getByLabelText("City"), "Atlanta");

        await user.click(screen.getByRole("tab", { name: "Invoice Settings" }));

        await user.type(await screen.findByLabelText("Default Payment Terms"), "15");
        await user.type(screen.getByLabelText("Default Tax Rate"), "7.25");
        await user.click(screen.getByRole("button", { name: "Card" }));
        await user.click(screen.getByRole("button", { name: "Bank" }));
        await user.type(screen.getByLabelText("Default Invoice Footer"), "Thanks for working with us.");

        expect(screen.getByLabelText("Invoice sender preview")).toHaveTextContent("Allen Studio");
        expect(screen.getByLabelText("Invoice sender preview")).toHaveTextContent("billing@example.com");
        expect(screen.getByLabelText("Invoice sender preview")).toHaveTextContent("Atlanta");
        expect(screen.getByLabelText("Invoice sender preview")).toHaveTextContent("Net 15");
        expect(screen.getByLabelText("Invoice sender preview")).toHaveTextContent("7.25%");
        expect(screen.getByLabelText("Invoice sender preview")).toHaveTextContent("Card, Bank");
        expect(screen.getByLabelText("Invoice sender preview")).toHaveTextContent("Thanks for working with us.");
    });

    it("loads and saves the profile through the api", async () => {
        const user = userEvent.setup();
        vi.mocked(getBusinessProfile).mockResolvedValueOnce({
            ...emptyProfile,
            id: 12,
            business_name: "Existing Studio",
            email: "existing@example.com",
        });

        render(<BusinessProfilePage />);

        expect(await screen.findAllByText("Existing Studio")).toHaveLength(2);
        await user.click(screen.getByRole("button", { name: "Edit Settings" }));

        expect(screen.getByDisplayValue("Existing Studio")).toBeInTheDocument();
        await user.clear(screen.getByLabelText("Business Name"));
        await user.type(screen.getByLabelText("Business Name"), "Updated Studio");

        await user.click(screen.getByRole("tab", { name: "Invoice Settings" }));

        await user.type(await screen.findByLabelText("Default Payment Terms"), "15");
        await user.type(screen.getByLabelText("Default Tax Rate"), "7.25");
        await user.click(screen.getByRole("button", { name: "Save Settings" }));

        expect(saveBusinessProfile).toHaveBeenCalledWith(
            expect.objectContaining({
                business_name: "Updated Studio",
                email: "existing@example.com",
                default_payment_terms_days: 15,
                default_tax_rate: "7.25",
            }),
        );
        expect(await screen.findByText("Profile saved.")).toBeInTheDocument();
        expect(screen.queryByRole("form", { name: "Business profile form" })).not.toBeInTheDocument();
        expect(screen.getByText("Updated Studio")).toBeInTheDocument();
    });
});
