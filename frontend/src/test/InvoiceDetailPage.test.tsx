import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { getCustomer, listCustomerLocations } from "../api/customers";
import { createInvoiceItem, deleteInvoiceItem, updateInvoiceItem } from "../api/invoiceItems";
import { getInvoice, updateInvoice, updateInvoiceStatus } from "../api/invoices";
import { createPayment, getPaymentSummary, listPayments } from "../api/payments";
import { createProduct, listProducts } from "../api/products";
import { addInvoiceTag, createTag, listInvoiceTags, listTags, removeInvoiceTag } from "../api/tags";
import { InvoiceDetailPage } from "../pages/InvoiceDetailPage";
import { formatDisplayDate, getDefaultSentInvoiceDueDate, getDefaultSentInvoiceIssuedDate } from "../utils/date";

vi.mock("../api/customers", () => ({
    getCustomer: vi.fn(),
    listCustomerLocations: vi.fn(),
}));

vi.mock("../api/invoices", () => ({
    getInvoice: vi.fn(),
    updateInvoice: vi.fn(),
    updateInvoiceStatus: vi.fn(),
}));

vi.mock("../api/invoiceItems", () => ({
    createInvoiceItem: vi.fn(),
    deleteInvoiceItem: vi.fn(),
    updateInvoiceItem: vi.fn(),
}));

vi.mock("../api/payments", () => ({
    PAYMENT_METHODS: ["cash", "card", "check", "bank_transfer", "other"],
    createPayment: vi.fn(),
    getPaymentSummary: vi.fn(),
    listPayments: vi.fn(),
}));

vi.mock("../api/products", () => ({
    createProduct: vi.fn(),
    listProducts: vi.fn(),
}));

vi.mock("../api/tags", () => ({
    addInvoiceTag: vi.fn(),
    createTag: vi.fn(),
    listInvoiceTags: vi.fn(),
    listTags: vi.fn(),
    removeInvoiceTag: vi.fn(),
}));

const mockedGetCustomer = vi.mocked(getCustomer);
const mockedListCustomerLocations = vi.mocked(listCustomerLocations);
const mockedCreateInvoiceItem = vi.mocked(createInvoiceItem);
const mockedDeleteInvoiceItem = vi.mocked(deleteInvoiceItem);
const mockedUpdateInvoiceItem = vi.mocked(updateInvoiceItem);
const mockedGetInvoice = vi.mocked(getInvoice);
const mockedUpdateInvoice = vi.mocked(updateInvoice);
const mockedUpdateInvoiceStatus = vi.mocked(updateInvoiceStatus);
const mockedCreatePayment = vi.mocked(createPayment);
const mockedGetPaymentSummary = vi.mocked(getPaymentSummary);
const mockedListPayments = vi.mocked(listPayments);
const mockedCreateProduct = vi.mocked(createProduct);
const mockedListProducts = vi.mocked(listProducts);
const mockedAddInvoiceTag = vi.mocked(addInvoiceTag);
const mockedCreateTag = vi.mocked(createTag);
const mockedListInvoiceTags = vi.mocked(listInvoiceTags);
const mockedListTags = vi.mocked(listTags);
const mockedRemoveInvoiceTag = vi.mocked(removeInvoiceTag);

function LocationDisplay() {
    const location = useLocation();
    const state = location.state as { fromInvoiceId?: number } | null;
    return (
        <>
            <span data-testid="location-path">{location.pathname}</span>
            <span data-testid="invoice-state">{state?.fromInvoiceId ?? ""}</span>
        </>
    );
}

describe("InvoiceDetailPage", () => {
    let printSpy: ReturnType<typeof vi.spyOn>;

    beforeEach(() => {
        vi.clearAllMocks();
        printSpy = vi.spyOn(window, "print").mockImplementation(() => {});

        mockedGetInvoice.mockResolvedValue({
            id: 7,
            customer_id: 1,
            location_id: 10,
            date_issued: "2026-06-01",
            date_due: "2026-07-01",
            total: 7500,
            status: "sent",
            cost_total_cents: 2000,
            profit_total_cents: 5500,
            profit_margin_percent: 73.33,
            items: [
                {
                    id: 11,
                    invoice_id: 7,
                    product_id: 3,
                    quantity: 2,
                    unit_cost_cents: 1000,
                    cost_total_cents: 2000,
                    unit_price_cents: 2500,
                    line_total_cents: 5000,
                    profit_total_cents: 3000,
                },
            ],
        });
        mockedGetCustomer.mockResolvedValue({
            id: 1,
            name: "John Doe",
            email: "john@example.com",
        });
        mockedListCustomerLocations.mockResolvedValue([
            {
                id: 10,
                customer_id: 1,
                location_id: 100,
                label: "Home",
                address_line1: "123 Main St",
                address_line2: null,
                city: "Orlando",
                state: "FL",
                postal_code: "32801",
                country: "US",
                is_primary: true,
                is_active: true,
                notes: null,
                created_at: "2026-01-01",
                updated_at: "2026-01-01",
            },
            {
                id: 20,
                customer_id: 1,
                location_id: 200,
                label: "Office",
                address_line1: "456 Office Rd",
                address_line2: null,
                city: "Orlando",
                state: "FL",
                postal_code: "32801",
                country: "US",
                is_primary: false,
                is_active: true,
                notes: null,
                created_at: "2026-01-01",
                updated_at: "2026-01-01",
            },
        ]);
        mockedUpdateInvoice.mockResolvedValue({
            id: 7,
            customer_id: 1,
            location_id: 20,
            date_issued: "2026-06-01",
            date_due: "2026-07-01",
            total: 7500,
            status: "sent",
        });
        mockedUpdateInvoiceStatus.mockResolvedValue({
            id: 7,
            customer_id: 1,
            location_id: 10,
            date_issued: "2026-06-01",
            date_due: "2026-07-01",
            total: 7500,
            status: "void",
        });
        mockedGetPaymentSummary.mockResolvedValue({
            invoice_id: 7,
            invoice_total_cents: 7500,
            amount_paid_cents: 2500,
            balance_due_cents: 5000,
            is_paid: false,
        });
        mockedListPayments.mockResolvedValue([
            {
                id: 9,
                invoice_id: 7,
                amount_cents: 2500,
                payment_date: "2026-06-15",
                method: "card",
                note: "Deposit",
            },
        ]);
        mockedCreatePayment.mockResolvedValue({
            id: 10,
            invoice_id: 7,
            amount_cents: 5000,
            payment_date: "2026-06-20",
            method: "check",
            note: "Final payment",
        });
        mockedListProducts.mockResolvedValue([
            {
                id: 3,
                name: "Consulting",
                description: null,
                cost_cents: 0,
                unit_price_cents: 2500,
                category_id: 2,
                category_name: "Labor",
                is_active: true,
            },
            {
                id: 4,
                name: "Hosting",
                description: null,
                cost_cents: 0,
                unit_price_cents: 1500,
                category_id: 3,
                category_name: "Infrastructure",
                is_active: true,
            },
        ]);
        mockedListTags.mockResolvedValue([
            {
                id: 1,
                name: "Commercial",
                description: null,
                is_active: true,
            },
        ]);
        mockedListInvoiceTags.mockResolvedValue([
            {
                id: 2,
                name: "Repair",
                description: null,
                is_active: true,
            },
        ]);
        mockedAddInvoiceTag.mockResolvedValue({
            invoice_id: 7,
            tag_id: 1,
            created_at: "2026-08-17T00:00:00",
        });
        mockedCreateTag.mockResolvedValue({
            id: 3,
            name: "Warranty",
            description: null,
            is_active: true,
        });
        mockedRemoveInvoiceTag.mockResolvedValue(undefined);
        mockedDeleteInvoiceItem.mockResolvedValue(undefined);
        mockedCreateInvoiceItem.mockResolvedValue({
            id: 12,
            invoice_id: 7,
            product_id: 4,
            quantity: 3,
            unit_cost_cents: 500,
            cost_total_cents: 1500,
            unit_price_cents: 1500,
            line_total_cents: 4500,
            profit_total_cents: 3000,
        });
        mockedCreateProduct.mockResolvedValue({
            id: 5,
            name: "Custom Work",
            description: null,
            cost_cents: 1000,
            unit_price_cents: 2500,
            category_id: 1,
            category_name: "Uncategorized",
            is_active: true,
        });
        mockedUpdateInvoiceItem.mockResolvedValue({
            id: 11,
            invoice_id: 7,
            product_id: 3,
            quantity: 5,
            unit_cost_cents: 1000,
            cost_total_cents: 5000,
            unit_price_cents: 2500,
            line_total_cents: 12500,
            profit_total_cents: 7500,
        });
    });

    afterEach(() => {
        vi.restoreAllMocks();
    });

    it("renders invoice detail with line items and payments", async () => {
        render(
            <MemoryRouter initialEntries={["/invoices/7"]}>
                <Routes>
                    <Route path="/invoices/:invoiceId" element={<InvoiceDetailPage />} />
                </Routes>
            </MemoryRouter>
        );

        expect(await screen.findByRole("heading", { name: "Invoice #7", level: 2 })).toBeInTheDocument();
        expect(mockedGetInvoice).toHaveBeenCalledWith(7, true);
        expect(mockedGetCustomer).toHaveBeenCalledWith(1);
        expect(mockedListPayments).toHaveBeenCalledWith(7);
        expect(mockedGetPaymentSummary).toHaveBeenCalledWith(7);
        expect(mockedListTags).toHaveBeenCalledWith(true);
        expect(mockedListInvoiceTags).toHaveBeenCalledWith(7);

        const summary = screen.getByLabelText("Invoice payment summary");
        expect(within(summary).getByText("$25")).toBeInTheDocument();
        expect(within(summary).getByText("$50")).toBeInTheDocument();
        expect(within(summary).getByText("$20")).toBeInTheDocument();
        expect(within(summary).getByText("$55")).toBeInTheDocument();
        expect(within(summary).queryByText("73.33%")).not.toBeInTheDocument();

        expect(screen.getAllByText("John Doe").length).toBeGreaterThan(0);
        expect(screen.getByRole("link", { name: "John Doe" })).toHaveAttribute("href", "/customers/1");
        expect(screen.getByRole("link", { name: /Home - 123 Main St/i })).toHaveAttribute("href", "/locations/100");
        expect(screen.getByRole("button", { name: "Edit invoice location" })).toBeInTheDocument();
        expect(screen.getAllByText("Jun-1-2026").length).toBeGreaterThan(0);
        expect(screen.getAllByText("Jul-1-2026").length).toBeGreaterThan(0);
        expect(screen.getAllByText("$75").length).toBeGreaterThan(0);
        expect(screen.getByText("1 items")).toBeInTheDocument();
        expect(screen.getAllByText("Consulting").length).toBeGreaterThan(0);
        expect(screen.getAllByText("Labor").length).toBeGreaterThan(0);
        expect(screen.getByText("Repair")).toBeInTheDocument();
        expect(screen.getByText("Deposit")).toBeInTheDocument();
        expect(screen.getByRole("button", { name: "Add Payment" })).toBeInTheDocument();
        expect(screen.getByRole("link", { name: "Back to invoices" })).toHaveAttribute("href", "/invoices");

	        const lineItemsHeadings = screen.getAllByRole("heading", { name: "Line Items" });
	        const lineItemsHeading = lineItemsHeadings[lineItemsHeadings.length - 1];
	        const lineItemsSection = lineItemsHeading.closest("section") as HTMLElement;
	        expect(
	            within(lineItemsSection)
	                .getAllByRole("columnheader")
	                .map((header) => header.textContent)
	        ).toEqual(["Product", "Category", "Unit Cost", "Total Cost", "Quantity", "Unit Price", "Total Price", "Profit"]);
	        const tagsHeading = screen.getByRole("heading", { name: "Tags" });
	        expect(lineItemsHeading.compareDocumentPosition(tagsHeading) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
	    });

    it("updates the invoice location from invoice detail", async () => {
        render(
            <MemoryRouter initialEntries={["/invoices/7"]}>
                <Routes>
                    <Route path="/invoices/:invoiceId" element={<InvoiceDetailPage />} />
                </Routes>
            </MemoryRouter>
        );

        fireEvent.click(await screen.findByRole("button", { name: "Edit invoice location" }));

        const dialog = await screen.findByRole("dialog", { name: "Edit Location" });
        expect(within(dialog).getByLabelText("Location")).toHaveValue("10");

        fireEvent.change(within(dialog).getByLabelText("Location"), { target: { value: "20" } });
        fireEvent.click(within(dialog).getByRole("button", { name: "Save Location" }));

        await waitFor(() => {
            expect(mockedUpdateInvoice).toHaveBeenCalledWith(7, {
                location_id: 20,
            });
        });
        expect(screen.queryByRole("dialog", { name: "Edit Location" })).not.toBeInTheDocument();
    });

    it("changes invoice status from invoice detail", async () => {
        render(
            <MemoryRouter initialEntries={["/invoices/7"]}>
                <Routes>
                    <Route path="/invoices/:invoiceId" element={<InvoiceDetailPage />} />
                </Routes>
            </MemoryRouter>
        );

        fireEvent.click(await screen.findByRole("button", { name: "Void" }));

        await waitFor(() => {
            expect(mockedUpdateInvoiceStatus).toHaveBeenCalledWith(7, "void");
        });
    });

    it("updates the invoice work description", async () => {
        render(
            <MemoryRouter initialEntries={["/invoices/7"]}>
                <Routes>
                    <Route path="/invoices/:invoiceId" element={<InvoiceDetailPage />} />
                </Routes>
            </MemoryRouter>
        );

        fireEvent.click(await screen.findByRole("button", { name: "Edit Description" }));

        const dialog = await screen.findByRole("dialog", { name: "Edit Description" });
        fireEvent.change(within(dialog).getByLabelText("Description"), {
            target: { value: "Installed mini split in upstairs bedroom." },
        });
        fireEvent.click(within(dialog).getByRole("button", { name: "Save Description" }));

        await waitFor(() => {
            expect(mockedUpdateInvoice).toHaveBeenCalledWith(7, {
                description: "Installed mini split in upstairs bedroom.",
            });
        });
    });

    it("opens a send drawer before sending a draft invoice", async () => {
        mockedGetInvoice.mockResolvedValue({
            id: 7,
            customer_id: 1,
            location_id: 10,
            date_issued: null,
            date_due: null,
            total: 7500,
            status: "draft",
            cost_total_cents: 2000,
            profit_total_cents: 5500,
            profit_margin_percent: 73.33,
            items: [],
        });

        render(
            <MemoryRouter initialEntries={["/invoices/7"]}>
                <Routes>
                    <Route path="/invoices/:invoiceId" element={<InvoiceDetailPage />} />
                </Routes>
            </MemoryRouter>
        );

        fireEvent.click(await screen.findByRole("button", { name: "Send" }));

        const drawer = await screen.findByRole("dialog", { name: "Send Invoice" });
        expect(within(drawer).getByText("John Doe")).toBeInTheDocument();
        expect(within(drawer).getByText("john@example.com")).toBeInTheDocument();
        expect(within(drawer).getByText(formatDisplayDate(getDefaultSentInvoiceDueDate()))).toBeInTheDocument();
        expect(within(drawer).getByText(formatDisplayDate(getDefaultSentInvoiceIssuedDate()))).toBeInTheDocument();
        expect(within(drawer).getByLabelText("Change due date")).toHaveValue(getDefaultSentInvoiceDueDate());
        expect(within(drawer).getByLabelText("Subject")).toHaveValue("Invoice #7");
        expect(within(drawer).getByLabelText("Note")).toHaveValue(
            "Thank you for your business. Please review the attached invoice when you have a moment."
        );

        fireEvent.change(within(drawer).getByLabelText("Change due date"), {
            target: { value: "2026-10-30" },
        });
        expect(within(drawer).getByText("Oct-30-2026")).toBeInTheDocument();
        fireEvent.click(within(drawer).getByRole("button", { name: "Preview Invoice" }));
        await waitFor(() => {
            expect(printSpy).toHaveBeenCalled();
        });
        expect(mockedUpdateInvoice).not.toHaveBeenCalled();
        fireEvent.change(within(drawer).getByLabelText("Note"), {
            target: { value: "Please review this invoice when you can." },
        });
        fireEvent.click(within(drawer).getByRole("button", { name: "Send Invoice" }));

        await waitFor(() => {
            expect(mockedUpdateInvoice).toHaveBeenCalledWith(7, {
                date_issued: getDefaultSentInvoiceIssuedDate(),
                date_due: "2026-10-30",
            });
        });
        await waitFor(() => {
            expect(mockedUpdateInvoiceStatus).toHaveBeenCalledWith(7, "sent");
        });
    });

    it("opens customer detail with invoice return context", async () => {
        render(
            <MemoryRouter initialEntries={["/invoices/7"]}>
                <Routes>
                    <Route path="/invoices/:invoiceId" element={<InvoiceDetailPage />} />
                    <Route path="/customers/:customerId" element={<LocationDisplay />} />
                </Routes>
            </MemoryRouter>
        );

        fireEvent.click(await screen.findByRole("link", { name: "John Doe" }));

        expect(screen.getByTestId("location-path")).toHaveTextContent("/customers/1");
        expect(screen.getByTestId("invoice-state")).toHaveTextContent("7");
    });

    it("opens location detail with invoice return context", async () => {
        render(
            <MemoryRouter initialEntries={["/invoices/7"]}>
                <Routes>
                    <Route path="/invoices/:invoiceId" element={<InvoiceDetailPage />} />
                    <Route path="/locations/:locationId" element={<LocationDisplay />} />
                </Routes>
            </MemoryRouter>
        );

        fireEvent.click(await screen.findByRole("link", { name: /Home - 123 Main St/i }));

        expect(screen.getByTestId("location-path")).toHaveTextContent("/locations/100");
        expect(screen.getByTestId("invoice-state")).toHaveTextContent("7");
    });

    it("opens tag detail with invoice return context", async () => {
        render(
            <MemoryRouter initialEntries={["/invoices/7"]}>
                <Routes>
                    <Route path="/invoices/:invoiceId" element={<InvoiceDetailPage />} />
                    <Route path="/tags/:tagId" element={<LocationDisplay />} />
                </Routes>
            </MemoryRouter>
        );

        fireEvent.click(await screen.findByRole("link", { name: "View Repair tag" }));

        expect(screen.getByTestId("location-path")).toHaveTextContent("/tags/2");
        expect(screen.getByTestId("invoice-state")).toHaveTextContent("7");
    });

    it("adds a payment from the payments section", async () => {
        render(
            <MemoryRouter initialEntries={["/invoices/7"]}>
                <Routes>
                    <Route path="/invoices/:invoiceId" element={<InvoiceDetailPage />} />
                </Routes>
            </MemoryRouter>
        );

        fireEvent.click(await screen.findByRole("button", { name: "Add Payment" }));

        const dialog = await screen.findByRole("dialog", { name: "Add Payment" });
        fireEvent.change(within(dialog).getByLabelText("Amount"), { target: { value: "50" } });
        fireEvent.change(within(dialog).getByLabelText("Payment Date"), { target: { value: "2026-06-20" } });
        fireEvent.change(within(dialog).getByLabelText("Method"), { target: { value: "check" } });
        fireEvent.change(within(dialog).getByLabelText("Note"), { target: { value: "Final payment" } });
        fireEvent.click(within(dialog).getByRole("button", { name: "Save Payment" }));

        await waitFor(() => {
            expect(mockedCreatePayment).toHaveBeenCalledWith(7, {
                amount_cents: 5000,
                payment_date: "2026-06-20",
                method: "check",
                note: "Final payment",
            });
        });
        expect(screen.queryByRole("dialog", { name: "Add Payment" })).not.toBeInTheDocument();
    });

    it("links back to the source customer when opened from customer detail", async () => {
        render(
            <MemoryRouter initialEntries={[{ pathname: "/invoices/7", state: { fromCustomerId: 1 } }]}>
                <Routes>
                    <Route path="/invoices/:invoiceId" element={<InvoiceDetailPage />} />
                </Routes>
            </MemoryRouter>
        );

        expect(await screen.findByRole("heading", { name: "Invoice #7", level: 2 })).toBeInTheDocument();
        expect(screen.getByRole("link", { name: "Back to customer" })).toHaveAttribute("href", "/customers/1");
    });

    it("renders a customer-facing print invoice layout", async () => {
        render(
            <MemoryRouter initialEntries={["/invoices/7"]}>
                <Routes>
                    <Route path="/invoices/:invoiceId" element={<InvoiceDetailPage />} />
                </Routes>
            </MemoryRouter>
        );

        const printableInvoice = await screen.findByLabelText("Printable customer invoice");

        expect(within(printableInvoice).getByRole("heading", { name: "Invoice #7" })).toBeInTheDocument();
	        expect(within(printableInvoice).getByText("Bill To")).toBeInTheDocument();
	        expect(within(printableInvoice).getByText("John Doe")).toBeInTheDocument();
	        expect(
	            within(printableInvoice)
	                .getAllByRole("columnheader")
	                .map((header) => header.textContent)
	        ).toEqual(["Product", "Unit Price", "Quantity", "Total Price"]);
	        expect(within(printableInvoice).getByRole("columnheader", { name: "Total Price" })).toBeInTheDocument();
	        expect(within(printableInvoice).getByText("Balance Due")).toBeInTheDocument();
	        expect(within(printableInvoice).queryByText("Category")).not.toBeInTheDocument();
	        expect(within(printableInvoice).queryByText("Labor")).not.toBeInTheDocument();
	        expect(within(printableInvoice).queryByText("Payments")).not.toBeInTheDocument();
	    });

    it("prints the invoice detail", async () => {
        const printSpy = vi.spyOn(window, "print").mockImplementation(() => undefined);

        render(
            <MemoryRouter initialEntries={["/invoices/7"]}>
                <Routes>
                    <Route path="/invoices/:invoiceId" element={<InvoiceDetailPage />} />
                </Routes>
            </MemoryRouter>
        );

        fireEvent.click(await screen.findByRole("button", { name: "Print" }));

        expect(printSpy).toHaveBeenCalledOnce();
        printSpy.mockRestore();
    });

    it("adds a line item to a draft invoice from detail", async () => {
        mockedGetInvoice.mockResolvedValue({
            id: 7,
            customer_id: 1,
            date_issued: "2026-06-01",
            date_due: "2026-07-01",
            total: 0,
            status: "draft",
            items: [],
        });

        render(
            <MemoryRouter initialEntries={["/invoices/7"]}>
                <Routes>
                    <Route path="/invoices/:invoiceId" element={<InvoiceDetailPage />} />
                </Routes>
            </MemoryRouter>
        );

        await screen.findByRole("heading", { name: "Invoice #7", level: 2 });
        fireEvent.click(screen.getByRole("button", { name: "Add Items" }));

        const dialog = await screen.findByRole("dialog", { name: "Add Items" });
        fireEvent.change(within(dialog).getByLabelText("Search Items"), { target: { value: "host" } });
        fireEvent.click(within(dialog).getByRole("checkbox", { name: /Hosting/i }));
        fireEvent.click(within(dialog).getByRole("button", { name: "Save Items" }));

        await waitFor(() => {
            expect(mockedCreateInvoiceItem).toHaveBeenCalledWith(7, {
                product_id: 4,
                quantity: 1,
                unit_cost_cents: null,
                unit_price_cents: null,
            });
        });
        expect(mockedGetInvoice).toHaveBeenCalledTimes(2);
        expect(mockedGetCustomer).toHaveBeenCalledTimes(1);
        expect(mockedListProducts).toHaveBeenCalledTimes(1);
        expect(mockedListTags).toHaveBeenCalledTimes(1);
    });

    it("creates a new product before adding a custom line item", async () => {
        mockedGetInvoice.mockResolvedValue({
            id: 7,
            customer_id: 1,
            date_issued: "2026-06-01",
            date_due: "2026-07-01",
            total: 0,
            status: "draft",
            items: [],
        });

        render(
            <MemoryRouter initialEntries={["/invoices/7"]}>
                <Routes>
                    <Route path="/invoices/:invoiceId" element={<InvoiceDetailPage />} />
                </Routes>
            </MemoryRouter>
        );

        await screen.findByRole("heading", { name: "Invoice #7", level: 2 });
        fireEvent.click(screen.getByRole("button", { name: "Add Items" }));

        const dialog = await screen.findByRole("dialog", { name: "Add Items" });
        fireEvent.change(within(dialog).getByLabelText("Name for new invoice detail item"), { target: { value: "Custom Work" } });
        fireEvent.change(within(dialog).getByLabelText("Cost for new invoice detail item"), { target: { value: "10" } });
        fireEvent.change(within(dialog).getByLabelText("Price for new invoice detail item"), { target: { value: "25" } });
        fireEvent.click(within(dialog).getByRole("button", { name: "Add New Item" }));

        expect(await within(dialog).findByRole("checkbox", { name: /Custom Work/i })).toBeChecked();
        fireEvent.click(within(dialog).getByRole("button", { name: "Save Items" }));

        await waitFor(() => {
            expect(mockedCreateProduct).toHaveBeenCalledWith({
                name: "Custom Work",
                cost_cents: 1000,
                unit_price_cents: 2500,
                is_active: true,
            });
            expect(mockedCreateInvoiceItem).toHaveBeenCalledWith(7, {
                product_id: 5,
                quantity: 1,
                unit_cost_cents: null,
                unit_price_cents: null,
            });
        });
    });

    it("merges matching line items by increasing quantity", async () => {
        mockedGetInvoice.mockResolvedValue({
            id: 7,
            customer_id: 1,
            date_issued: "2026-06-01",
            date_due: "2026-07-01",
            total: 5000,
            status: "draft",
            cost_total_cents: 2000,
            profit_total_cents: 3000,
            profit_margin_percent: 60,
            items: [
                {
                    id: 11,
                    invoice_id: 7,
                    product_id: 3,
                    quantity: 2,
                    unit_cost_cents: 1000,
                    cost_total_cents: 2000,
                    unit_price_cents: 2500,
                    line_total_cents: 5000,
                    profit_total_cents: 3000,
                },
            ],
        });
        mockedListProducts.mockResolvedValue([
            {
                id: 3,
                name: "Consulting",
                description: null,
                cost_cents: 1000,
                unit_price_cents: 2500,
                category_id: 2,
                category_name: "Labor",
                is_active: true,
            },
        ]);

        render(
            <MemoryRouter initialEntries={["/invoices/7"]}>
                <Routes>
                    <Route path="/invoices/:invoiceId" element={<InvoiceDetailPage />} />
                </Routes>
            </MemoryRouter>
        );

        await screen.findByRole("heading", { name: "Invoice #7", level: 2 });
        fireEvent.click(screen.getByRole("button", { name: "Add Items" }));

        const dialog = await screen.findByRole("dialog", { name: "Add Items" });
        fireEvent.click(within(dialog).getByRole("checkbox", { name: /Consulting/i }));
        fireEvent.click(within(dialog).getByRole("button", { name: "Save Items" }));

        await waitFor(() => {
            expect(mockedUpdateInvoiceItem).toHaveBeenCalledWith(11, {
                quantity: 3,
            });
        });
        expect(mockedCreateInvoiceItem).not.toHaveBeenCalled();
    });

    it("deletes a draft invoice line item", async () => {
        mockedGetInvoice.mockResolvedValue({
            id: 7,
            customer_id: 1,
            date_issued: "2026-06-01",
            date_due: "2026-07-01",
            total: 5000,
            status: "draft",
            cost_total_cents: 2000,
            profit_total_cents: 3000,
            profit_margin_percent: 60,
            items: [
                {
                    id: 11,
                    invoice_id: 7,
                    product_id: 3,
                    quantity: 2,
                    unit_cost_cents: 1000,
                    cost_total_cents: 2000,
                    unit_price_cents: 2500,
                    line_total_cents: 5000,
                    profit_total_cents: 3000,
                },
            ],
        });

        render(
            <MemoryRouter initialEntries={["/invoices/7"]}>
                <Routes>
                    <Route path="/invoices/:invoiceId" element={<InvoiceDetailPage />} />
                </Routes>
            </MemoryRouter>
        );

        await screen.findByRole("heading", { name: "Invoice #7", level: 2 });
        fireEvent.click(screen.getByRole("button", { name: "Delete" }));

        await waitFor(() => {
            expect(mockedDeleteInvoiceItem).toHaveBeenCalledWith(11);
        });
    });

    it("increments and decrements a draft invoice line item quantity", async () => {
        mockedGetInvoice.mockResolvedValue({
            id: 7,
            customer_id: 1,
            date_issued: "2026-06-01",
            date_due: "2026-07-01",
            total: 5000,
            status: "draft",
            cost_total_cents: 2000,
            profit_total_cents: 3000,
            profit_margin_percent: 60,
            items: [
                {
                    id: 11,
                    invoice_id: 7,
                    product_id: 3,
                    quantity: 2,
                    unit_cost_cents: 1000,
                    cost_total_cents: 2000,
                    unit_price_cents: 2500,
                    line_total_cents: 5000,
                    profit_total_cents: 3000,
                },
            ],
        });

        render(
            <MemoryRouter initialEntries={["/invoices/7"]}>
                <Routes>
                    <Route path="/invoices/:invoiceId" element={<InvoiceDetailPage />} />
                </Routes>
            </MemoryRouter>
        );

        await screen.findByRole("heading", { name: "Invoice #7", level: 2 });
        fireEvent.click(screen.getByRole("button", { name: "Increase quantity for Consulting" }));

        await waitFor(() => {
            expect(mockedUpdateInvoiceItem).toHaveBeenCalledWith(11, {
                quantity: 3,
            });
        });

        fireEvent.click(screen.getByRole("button", { name: "Decrease quantity for Consulting" }));

        await waitFor(() => {
            expect(mockedUpdateInvoiceItem).toHaveBeenCalledWith(11, {
                quantity: 1,
            });
        });
    });

    it("adds and removes invoice tags from detail", async () => {
        render(
            <MemoryRouter initialEntries={["/invoices/7"]}>
                <Routes>
                    <Route path="/invoices/:invoiceId" element={<InvoiceDetailPage />} />
                </Routes>
            </MemoryRouter>
        );

        await screen.findByRole("heading", { name: "Invoice #7", level: 2 });
        expect(screen.getByRole("link", { name: "View Repair tag" })).toHaveAttribute("href", "/tags/2");

        fireEvent.click(screen.getByRole("button", { name: "Manage Tags" }));

        const dialog = await screen.findByRole("dialog", { name: "Manage Tags" });
        expect(within(dialog).getByLabelText("Repair")).toBeChecked();
        fireEvent.change(within(dialog).getByLabelText("Search Tags"), { target: { value: "com" } });
        expect(within(dialog).getByLabelText("Commercial")).toBeInTheDocument();
        expect(within(dialog).queryByLabelText("Repair")).not.toBeInTheDocument();
        fireEvent.click(within(dialog).getByLabelText("Commercial"));
        fireEvent.change(within(dialog).getByLabelText("Name for new invoice tag"), { target: { value: "Warranty" } });
        fireEvent.click(within(dialog).getByRole("button", { name: "Add New Tag" }));

        await waitFor(() => {
            expect(mockedCreateTag).toHaveBeenCalledWith({
                name: "Warranty",
                is_active: true,
            });
        });

        expect(within(dialog).getByLabelText("Warranty")).toBeChecked();
        fireEvent.click(within(dialog).getByRole("button", { name: "Save Tags" }));

        await waitFor(() => {
            expect(mockedAddInvoiceTag).toHaveBeenCalledWith(7, { tag_id: 1 });
            expect(mockedAddInvoiceTag).toHaveBeenCalledWith(7, { tag_id: 3 });
        });

        fireEvent.click(screen.getByRole("button", { name: "Remove Repair tag" }));

        await waitFor(() => {
            expect(mockedRemoveInvoiceTag).toHaveBeenCalledWith(7, 2);
        });
        expect(mockedGetInvoice).toHaveBeenCalledTimes(1);
        expect(mockedGetCustomer).toHaveBeenCalledTimes(1);
        expect(mockedListInvoiceTags).toHaveBeenCalledTimes(3);
    });
});
