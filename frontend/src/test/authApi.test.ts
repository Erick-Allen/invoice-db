import { describe, expect, it, vi } from "vitest";
import { continueAsGuest } from "../api/auth";
import { apiRequest } from "../api/client";

vi.mock("../api/client", () => ({
    apiRequest: vi.fn(),
}));

const mockedApiRequest = vi.mocked(apiRequest);

describe("auth api", () => {
    it("creates guest access through the shared api client", async () => {
        mockedApiRequest.mockResolvedValueOnce({
            isAuthenticated: true,
            isGuest: true,
            workspaceId: 1,
            guestExpiresAt: "2026-10-05T00:00:00+00:00",
            user: {
                id: 1,
                email: null,
                name: "Guest",
                is_guest: true,
                workspace_id: 1,
                guest_expires_at: "2026-10-05T00:00:00+00:00",
            },
        });

        await continueAsGuest();

        expect(mockedApiRequest).toHaveBeenCalledWith("/auth/guest/", {
            method: "POST",
        });
    });
});
