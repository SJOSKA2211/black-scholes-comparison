"use client";
import { useCallback } from "react";
import { createBrowserClient } from "@/lib/supabase/client";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchWithAuth<T>(
  path: string,
  options: RequestInit = {},
  token: string | null
): Promise<T> {
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };
  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail ?? `HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

/**
 * Returns a typed fetch function pre-populated with the current
 * Supabase session JWT. Used by React Query queryFn callbacks.
 */
export function useApi() {
  const supabase = createBrowserClient();

  const getToken = useCallback(async (): Promise<string | null> => {
    const { data } = await supabase.auth.getSession();
    return data.session?.access_token ?? null;
  }, [supabase]);

  const get = useCallback(async <T>(path: string): Promise<T> => {
    const token = await getToken();
    return fetchWithAuth<T>(path, { method: "GET" }, token);
  }, [getToken]);

  const post = useCallback(async <T>(path: string, body: unknown): Promise<T> => {
    const token = await getToken();
    return fetchWithAuth<T>(path, { method: "POST",
      body: JSON.stringify(body) }, token);
  }, [getToken]);

  const downloadBlob = useCallback(async (path: string): Promise<Blob> => {
    const token = await getToken();
    const res = await fetch(`${API_BASE}${path}`,
      { headers: token ? { Authorization: `Bearer ${token}` } : {} });
    if (!res.ok) throw new Error(`Download HTTP ${res.status}`);
    return res.blob();
  }, [getToken]);

  return { get, post, downloadBlob };
}
