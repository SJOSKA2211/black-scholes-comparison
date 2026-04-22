"use client";
import { useRealtime } from "@/hooks/useRealtime";
import { cn } from "@/lib/utils";

export function RealtimeBadge() {
  // Subscribe to a generic channel to monitor connection status
  const { connected } = useRealtime({ 
    table: "notifications", 
    onData: () => {} 
  });

  return (
    <div className="flex items-center gap-3 px-4 py-2 rounded-2xl bg-slate-900/50 border border-slate-800">
      <div className="relative flex items-center justify-center">
        <div className={cn(
          "w-2 h-2 rounded-full transition-all duration-500",
          connected ? "bg-emerald-500" : "bg-red-500"
        )} />
        {connected && (
          <div className="absolute w-2 h-2 rounded-full bg-emerald-500 animate-ping opacity-75" />
        )}
      </div>
      <span className={cn(
        "text-[10px] font-bold uppercase tracking-widest",
        connected ? "text-emerald-500" : "text-red-500"
      )}>
        {connected ? "Realtime Live" : "Sync Lost"}
      </span>
    </div>
  );
}
