"use client";
import { useCallback } from "react";
import { apiFetch } from "@/lib/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * React hook wrapper for the standalone API client.
 * Provides memoized fetch methods for use in components.
 */
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

  const patch = useCallback(
    async <T>(path: string, body: unknown) =>
      apiFetch<T>(path, { method: "PATCH", body: JSON.stringify(body) }),
    [],
  );

  const del = useCallback(
    async <T>(path: string) => apiFetch<T>(path, { method: "DELETE" }),
    [],
  );

  const downloadBlob = useCallback(async (path: string): Promise<Blob> => {
    // For direct binary downloads from FastAPI/MinIO
    const res = await fetch(`${API_BASE}${path}`);
    if (!res.ok) throw new Error(`Download HTTP ${res.status}`);
    return res.blob();
  }, []);

  return { get, post, patch, delete: del, downloadBlob };
}
