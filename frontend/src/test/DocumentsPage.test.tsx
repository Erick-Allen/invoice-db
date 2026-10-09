import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import {
    createDocument,
    deleteDocument,
    listDocuments,
    updateDocument,
    type BusinessDocument,
} from "../api/documents";
import { DocumentsPage } from "../pages/DocumentsPage";

vi.mock("../api/documents", () => ({
    createDocument: vi.fn(),
    deleteDocument: vi.fn(),
    listDocuments: vi.fn(),
    updateDocument: vi.fn(),
}));

const documentContent = {
    type: "doc" as const,
    content: [
        {
            type: "paragraph",
            content: [{ type: "text", text: "Use nitrogen before brazing." }],
        },
    ],
};

const existingDocument: BusinessDocument = {
    id: 7,
    workspace_id: 1,
    title: "Refrigeration Checklist",
    category: "Service",
    content_json: documentContent,
    content_text: "Use nitrogen before brazing.",
    created_at: "2026-10-08 03:00:00",
    updated_at: "2026-10-08 03:00:00",
};

describe("DocumentsPage", () => {
    beforeEach(() => {
        vi.mocked(createDocument).mockReset();
        vi.mocked(deleteDocument).mockReset();
        vi.mocked(listDocuments).mockReset();
        vi.mocked(updateDocument).mockReset();
        vi.mocked(listDocuments).mockResolvedValue([existingDocument]);
        vi.mocked(updateDocument).mockImplementation(async (_documentId, payload) => ({
            ...existingDocument,
            title: payload.title ?? existingDocument.title,
            category: payload.category ?? existingDocument.category,
            content_json: payload.content_json ?? existingDocument.content_json,
        }));
        vi.mocked(createDocument).mockImplementation(async (payload) => ({
            ...existingDocument,
            id: 8,
            title: payload.title,
            category: payload.category || "General",
            content_json: payload.content_json,
            content_text: "",
        }));
    });

    it("loads documents and saves edits through the api", async () => {
        const user = userEvent.setup();

        render(<DocumentsPage />);

        expect(await screen.findByRole("button", { name: /Refrigeration Checklist/ })).toBeInTheDocument();
        expect(screen.getByRole("button", { name: "Edit" })).toBeInTheDocument();
        expect(screen.queryByDisplayValue("Refrigeration Checklist")).not.toBeInTheDocument();

        await user.click(screen.getByRole("button", { name: "Edit" }));

        expect(screen.getByDisplayValue("Refrigeration Checklist")).toBeInTheDocument();

        await user.clear(screen.getByLabelText("Title"));
        await user.type(screen.getByLabelText("Title"), "Updated Checklist");
        expect(screen.getByText("Unsaved changes")).toBeInTheDocument();
        await user.click(screen.getByRole("button", { name: "Save Document" }));

        expect(updateDocument).toHaveBeenCalledWith(
            7,
            expect.objectContaining({
                title: "Updated Checklist",
                category: "Service",
            }),
        );
        expect(await screen.findByText("Document saved.")).toBeInTheDocument();
        expect(screen.queryByText("Saved")).not.toBeInTheDocument();
        expect(screen.getByRole("button", { name: "Edit" })).toBeInTheDocument();
    });

    it("creates a new document from the empty editor state", async () => {
        const user = userEvent.setup();

        render(<DocumentsPage />);

        await user.click(await screen.findByRole("button", { name: "New" }));
        await user.type(screen.getByLabelText("Title"), "Overdue Customer Policy");
        await user.clear(screen.getByLabelText("Category"));
        await user.type(screen.getByLabelText("Category"), "Policy");
        await user.click(screen.getByRole("button", { name: "Save Document" }));

        expect(createDocument).toHaveBeenCalledWith(
            expect.objectContaining({
                title: "Overdue Customer Policy",
                category: "Policy",
                content_json: expect.objectContaining({ type: "doc" }),
            }),
        );
    });

    it("filters documents by search text", async () => {
        vi.mocked(listDocuments).mockResolvedValueOnce([
            existingDocument,
            {
                ...existingDocument,
                id: 9,
                title: "Payment Follow Up",
                category: "Policy",
                content_text: "Call overdue customers after seven days.",
            },
        ]);

        const user = userEvent.setup();

        render(<DocumentsPage />);

        expect(await screen.findByRole("button", { name: /Refrigeration Checklist/ })).toBeInTheDocument();
        expect(screen.getByRole("button", { name: /Payment Follow Up/ })).toBeInTheDocument();

        await user.type(screen.getByLabelText("Search"), "overdue");

        expect(screen.queryByRole("button", { name: /Refrigeration Checklist/ })).not.toBeInTheDocument();
        expect(screen.getByRole("button", { name: /Payment Follow Up/ })).toBeInTheDocument();
    });
});
