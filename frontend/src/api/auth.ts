import { apiRequest } from "./client";

export type AuthUser = {
    id: number;
    email: string;
    name: string;
};

export type AuthResponse = {
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

export function logout() {
    return apiRequest<void>("/auth/logout/", {
        method: "POST",
    });
}

export function getCurrentUser() {
    return apiRequest<AuthResponse>("/auth/me/");
}
