"use client";
import { useRealtime } from "@/hooks/useRealtime";
import { Wifi, WifiOff } from "lucide-react";

export default function ConnectionStatus() {
  // Subscribe to a generic heartbeat table or just check connection status
  const { connected } = useRealtime({
    table: "audit_log", // Minimal overhead table for monitoring
    onData: () => {},
  });

  return (
    <div className={`flex items-center gap-2 rounded-full px-2.5 py-1 text-[10px] font-bold uppercase tracking-widest transition-all ${
      connected 
        ? "bg-green-500/10 text-green-500 border border-green-500/20" 
        : "bg-red-500/10 text-red-500 border border-red-500/20"
    }`}>
      {connected ? (
        <>
          <Wifi className="h-3 w-3" />
          <span>Realtime Active</span>
        </>
      ) : (
        <>
          <WifiOff className="h-3 w-3" />
          <span>Disconnected</span>
        </>
      )}
    </div>
  );
}
