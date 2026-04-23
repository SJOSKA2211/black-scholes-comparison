"use client";
import { useEffect, useState, useRef } from "react";
import { createBrowserClient } from "@/lib/supabase/client";

type RealtimeEvent = "INSERT" | "UPDATE" | "DELETE" | "*";

interface UseRealtimeOptions<T> {
  table: string;
  event?: RealtimeEvent;
  filter?: string; // PostgREST syntax e.g. "user_id=eq.abc"
  onData: (payload: T) => void;
}

/** Subscribe to Supabase Realtime on any table with any event/filter. */
export function useRealtime<T extends object>({
  table,
  event = "*",
  filter,
  onData,
}: UseRealtimeOptions<T>) {
  const supabase = createBrowserClient();
  const [connected, setConnected] = useState(false);
  const callbackRef = useRef(onData);

  useEffect(() => {
    callbackRef.current = onData;
  }, [onData]);

  useEffect(() => {
    const name = filter
      ? `${table}_${filter.replace(/[^a-z0-9]/gi, "_")}`
      : table;
    const ch = supabase
      .channel(name)
      .on(
        "postgres_changes",
        { event, schema: "public", table, ...(filter ? { filter } : {}) },
        (payload) => {
          if (payload.new) callbackRef.current(payload.new as T);
        },
      )
      .subscribe((s) => setConnected(s === "SUBSCRIBED"));
    return () => {
      supabase.removeChannel(ch);
    };
  }, [table, event, filter, supabase]);

  return { connected };
}
