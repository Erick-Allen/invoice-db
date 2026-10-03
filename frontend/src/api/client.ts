const configuredApiBaseUrl =
    import.meta.env.VITE_API_BASE_URL ?? import.meta.env.VITE_APIBASE_URL;

const localApiBaseUrl =
    typeof window === "undefined"
        ? "http://127.0.0.1:8000/api"
        : `${window.location.protocol}//${window.location.hostname}:8000/api`;

const API_BASE_URL = configuredApiBaseUrl ?? localApiBaseUrl;
const CSRF_METHODS = new Set(["POST", "PUT", "PATCH", "DELETE"]);

function getCookie(name: string) {
    if (typeof document === "undefined") {
        return null;
    }

    const cookie = document.cookie
        .split("; ")
        .find((cookie) => cookie.startsWith(`${name}=`));

    return cookie ? decodeURIComponent(cookie.split("=").slice(1).join("=")) : null;
}

export async function apiRequest<T>(
    path: string,
    options: RequestInit = {}
): Promise<T> {
    const method = (options.method ?? "GET").toUpperCase();
    const csrfToken = CSRF_METHODS.has(method) ? getCookie("csrftoken") : null;

    const response = await fetch(`${API_BASE_URL}${path}`, {
        credentials: "include",
        headers: {
            "Content-Type": "application/json",
            ...(csrfToken ? { "X-CSRFToken": csrfToken } : {}),
            ...(options.headers ?? {}), 
        },
        ...options,
    });

    if (!response.ok) {
        let message = `Request failed with status ${response.status}`;


    try {
        const errorBody = await response.json();
        message =
            errorBody.detail ??
            errorBody.error ??
            JSON.stringify(errorBody);
    } catch {
        // Keep the default status message when the response is not JSON.
    }

    throw new Error(message);
}

if (response.status === 204) {
    return undefined as T;
}

    return response.json() as Promise<T>
}
