"use client";
import { useCallback } from "react";
import { createBrowserClient } from "@/lib/supabase/client";

const API_BASE = process.env.NEXT_PUBLIC_API_URL!;

async function apiFetch<T>(
  path: string,
  init: RequestInit,
  token: string | null,
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init.headers,
    },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail ?? `HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export function useApi() {
  const supabase = createBrowserClient();

  const getToken = useCallback(async () => {
    if (process.env.NEXT_PUBLIC_SKIP_AUTH === "true") {
      return "test-token";
    }
    const { data } = await supabase.auth.getSession();
    return data.session?.access_token ?? null;
  }, [supabase]);

  const get = useCallback(
    async <T>(path: string) =>
      apiFetch<T>(path, { method: "GET" }, await getToken()),
    [getToken],
  );

  const post = useCallback(
    async <T>(path: string, body: unknown) =>
      apiFetch<T>(
        path,
        { method: "POST", body: JSON.stringify(body) },
        await getToken(),
      ),
    [getToken],
  );

  const downloadBlob = useCallback(
    async (path: string): Promise<Blob> => {
      const token = await getToken();
      const res = await fetch(`${API_BASE}${path}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) throw new Error(`Download HTTP ${res.status}`);
      return res.blob();
    },
    [getToken],
  );

  return { get, post, downloadBlob };
}
