import { describe, expect, it, vi } from "vitest";
import { askAssistant } from "../api/assistant";
import { apiRequest } from "../api/client";

vi.mock("../api/client", () => ({
    apiRequest: vi.fn(),
}));

const mockedApiRequest = vi.mocked(apiRequest);

describe("assistant api", () => {
    it("uses the shared api client so session cookies are included", async () => {
        mockedApiRequest.mockResolvedValueOnce({ assistant_response: { message: "ok" } });

        await askAssistant("Show draft invoices");

        expect(mockedApiRequest).toHaveBeenCalledWith("/assistant/query/", {
            method: "POST",
            body: JSON.stringify({ message: "Show draft invoices" }),
        });
    });
});
