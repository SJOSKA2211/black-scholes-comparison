"use client";

import React, { useState } from "react";
import { Download } from "lucide-react";
import { useApi } from "@/hooks/useApi";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

interface DownloadButtonProps {
  resource: "experiments" | "market_data" | "scrapers";
  format?: "csv" | "json" | "xlsx";
  label?: string;
  variant?: "primary" | "outline" | "ghost";
}

/**
 * Universal Download Button.
 * Interacts with /api/v1/download/{resource} and handles redirection
 * to the presigned MinIO URL returned by the backend.
 */
export function DownloadButton({
  resource,
  format = "csv",
  label = "Download",
  variant = "outline",
}: DownloadButtonProps) {
  const [isDownloading, setIsDownloading] = useState(false);
  const { get } = useApi();

  const handleDownload = async () => {
    setIsDownloading(true);
    try {
      const response = await get<{ url: string; filename: string }>(
        `/download/${resource}?format=${format}`
      );
      
      // Redirect to the presigned URL for direct browser download
      window.location.href = response.url;
      
      toast.success(`Download started: ${response.filename}`);
    } catch (error) {
      console.error("Download failed:", error);
      toast.error("Failed to generate download. Please try again.");
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <Button
      variant={variant}
      size="sm"
      onClick={handleDownload}
      disabled={isDownloading}
      className="flex items-center gap-2"
    >
      <Download className={`h-4 w-4 ${isDownloading ? "animate-pulse" : ""}`} />
      {isDownloading ? "Generating..." : label}
    </Button>
  );
}
