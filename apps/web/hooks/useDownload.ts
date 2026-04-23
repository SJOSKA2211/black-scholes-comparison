"use client";
import { useState } from "react";
import { useApi } from "./useApi";

type Format = "csv" | "json" | "xlsx";
type Resource = "experiments" | "market-data" | "validation";

export function useDownload(
  resource: Resource,
  filters?: Record<string, string>,
) {
  const { downloadBlob } = useApi();
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const download = async (format: Format) => {
    setDownloading(true);
    setError(null);
    try {
      const qs = new URLSearchParams({ format, ...filters }).toString();
      const blob = await downloadBlob(`/api/v1/download/${resource}?${qs}`);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${resource}_${Date.now()}.${format}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Download failed");
    } finally {
      setDownloading(false);
    }
  };

  return { download, downloading, error };
}
