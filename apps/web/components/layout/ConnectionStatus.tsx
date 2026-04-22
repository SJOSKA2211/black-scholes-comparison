"use client";

import { motion } from "framer-motion";
import { useWebSocket } from "@/hooks/useWebSocket";
import { Wifi, WifiOff, Loader2 } from "lucide-react";

export function ConnectionStatus() {
  const { status } = useWebSocket<any>({ 
    channel: "metrics", 
    onMessage: () => {} 
  });

  const config = {
    open: { label: "Live", color: "bg-emerald-500", icon: Wifi, text: "text-emerald-400" },
    connecting: { label: "Connecting", color: "bg-amber-500", icon: Loader2, text: "text-amber-400" },
    closed: { label: "Offline", color: "bg-rose-500", icon: WifiOff, text: "text-rose-400" },
  };

  const current = config[status] || config.connecting;
  const Icon = current.icon;

  return (
    <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-900/50 border border-white/5">
      <div className="relative flex h-2 w-2">
        {status === "open" && (
          <span className={`animate-ping absolute inline-flex h-full w-full rounded-full ${current.color} opacity-75`} />
        )}
        <span className={`relative inline-flex rounded-full h-2 w-2 ${current.color}`} />
      </div>
      <span className={`text-[11px] font-bold uppercase tracking-widest ${current.text}`}>
        {current.label}
      </span>
      {status === "connecting" && (
        <Loader2 className="w-3 h-3 text-amber-400 animate-spin" />
      )}
    </div>
  );
}
