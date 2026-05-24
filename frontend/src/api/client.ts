const API_BASE_URL = import.meta.env.VITE_APIBASE_URL ?? "http://127.0.0.1:8000/api"

export async function apiRequest<T>(
    path: string,
    options: RequestInit = {}
): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${path}`, {
        headers: {
            "Content-Type": "application/json",
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
        
    }

    throw new Error(message);
}

if (response.status === 204) {
    return undefined as T;
}

    return response.json() as Promise<T>
}