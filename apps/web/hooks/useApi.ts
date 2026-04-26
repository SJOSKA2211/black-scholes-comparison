"use client";
import { useCallback } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL!;

async function apiFetch<T>(path: string, init: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
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
  const get = useCallback(
    async <T>(path: string) => apiFetch<T>(path, { method: "GET" }),
    [],
  );

  const post = useCallback(
    async <T>(path: string, body: unknown) =>
      apiFetch<T>(path, { method: "POST", body: JSON.stringify(body) }),
    [],
  );

  const downloadBlob = useCallback(async (path: string): Promise<Blob> => {
    const res = await fetch(`${API_BASE}${path}`);
    if (!res.ok) throw new Error(`Download HTTP ${res.status}`);
    return res.blob();
  }, []);

  return { get, post, downloadBlob };
}
