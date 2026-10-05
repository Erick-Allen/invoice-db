import { apiRequest } from "./client";

export type AuthUser = {
    id: number;
    email: string | null;
    name: string;
    is_guest: boolean;
    workspace_id: number;
    guest_expires_at: string | null;
};

export type AuthResponse = {
    isAuthenticated: boolean;
    isGuest: boolean;
    workspaceId: number;
    guestExpiresAt: string | null;
    user: AuthUser;
};

export type LoginPayload = {
    email: string;
    password: string;
};

export type SignupPayload = LoginPayload & {
    name?: string;
};

export function signup(payload: SignupPayload) {
    return apiRequest<AuthResponse>("/auth/signup/", {
        method: "POST",
        body: JSON.stringify(payload),
    });
}

export function login(payload: LoginPayload) {
    return apiRequest<AuthResponse>("/auth/login/", {
        method: "POST",
        body: JSON.stringify(payload),
    });
}

export function continueAsGuest() {
    return apiRequest<AuthResponse>("/auth/guest/", {
        method: "POST",
    });
}

export function logout() {
    return apiRequest<void>("/auth/logout/", {
        method: "POST",
    });
}

export function getCurrentUser() {
    return apiRequest<AuthResponse>("/auth/me/");
}
