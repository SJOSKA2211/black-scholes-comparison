/**
 * Standalone API client for the Black-Scholes Research Platform.
 * Used for server-side fetching and reusable API logic.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL!;

export interface ApiError {
  detail: string;
}

/**
 * Generic fetch wrapper with authentication and error handling.
 */
export async function apiFetch<T>(
  path: string,
  init?: RequestInit,
  token?: string | null,
): Promise<T> {
  const url = `${API_BASE}${path.startsWith("/") ? path : "/" + path}`;

  const headers = new Headers(init?.headers);
  headers.set("Content-Type", "application/json");
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(url, {
    ...init,
    headers,
  });

  if (!response.ok) {
    const errorData: ApiError = await response
      .json()
      .catch(() => ({ detail: response.statusText }));
    throw new Error(
      errorData.detail || `API request failed with status ${response.status}`,
    );
  }

  return response.json() as Promise<T>;
}

/**
 * Type-safe API methods.
 */
export const api = {
  get: <T>(path: string, token?: string | null) =>
    apiFetch<T>(path, { method: "GET" }, token),

  post: <T>(path: string, body: unknown, token?: string | null) =>
    apiFetch<T>(path, { method: "POST", body: JSON.stringify(body) }, token),

  patch: <T>(path: string, body: unknown, token?: string | null) =>
    apiFetch<T>(path, { method: "PATCH", body: JSON.stringify(body) }, token),

  delete: <T>(path: string, token?: string | null) =>
    apiFetch<T>(path, { method: "DELETE" }, token),
};
