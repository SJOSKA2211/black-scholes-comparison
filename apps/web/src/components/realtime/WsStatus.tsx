"use client";

import React from "react";
import { Wifi, WifiOff, Loader2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";

interface WsStatusProps {
  status: "connecting" | "open" | "closed";
}

/**
 * Visual indicator of the FastAPI WebSocket connection status.
 */
export function WsStatus({ status }: WsStatusProps) {
  const config = {
    connecting: {
      label: "Connecting",
      icon: <Loader2 className="h-3 w-3 animate-spin" />,
      variant: "outline" as const,
      className: "border-yellow-500/50 text-yellow-500 bg-yellow-500/10",
    },
    open: {
      label: "Live",
      icon: <Wifi className="h-3 w-3" />,
      variant: "outline" as const,
      className: "border-emerald-500/50 text-emerald-500 bg-emerald-500/10",
    },
    closed: {
      label: "Offline",
      icon: <WifiOff className="h-3 w-3" />,
      variant: "outline" as const,
      className: "border-red-500/50 text-red-500 bg-red-500/10",
    },
  };

  const current = config[status];

  return (
    <Badge
      variant={current.variant}
      className={`flex items-center gap-1.5 px-2 py-0.5 font-medium transition-all duration-300 ${current.className}`}
    >
      {current.icon}
      <span>{current.label}</span>
    </Badge>
  );
}
