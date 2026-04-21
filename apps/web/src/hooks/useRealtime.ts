"use client";
import { useEffect, useState } from "react";
import { createBrowserClient } from "@/lib/supabase/client";
import type { RealtimePostgresChangesPayload } from "@supabase/supabase-js";

type RealtimeEvent = "INSERT" | "UPDATE" | "DELETE" | "*";

interface UseRealtimeOptions<T> {
  table: string;
  event?: RealtimeEvent;
  filter?: string;                    // e.g. "user_id=eq.abc123"
  onData: (payload: T) => void;
}

/**
 * Subscribe to Supabase Realtime changes on any table.
 * Cleans up the channel subscription on unmount.
 */
export function useRealtime<T extends Record<string, unknown>>(
  { table, event = "*", filter, onData }: UseRealtimeOptions<T>
) {
  const supabase = createBrowserClient();
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    const channelName = filter
      ? `${table}_${filter.replace(/[^a-z0-9]/gi, "_")}` : table;

    const channel = supabase.channel(channelName)
      .on("postgres_changes", {
        event,
        schema: "public",
        table,
        ...(filter ? { filter } : {}),
      }, (payload: RealtimePostgresChangesPayload<T>) => {
        if (payload.new) onData(payload.new as T);
      })
      .subscribe((status) => {
        setConnected(status === "SUBSCRIBED");
      });

    return () => { 
      supabase.removeChannel(channel); 
    };
  }, [table, event, filter, onData, supabase]);

  return { connected };
}
