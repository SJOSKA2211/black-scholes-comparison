"use client";
import { useEffect, useRef, useCallback, useState } from "react";
import { createBrowserClient } from "@/lib/supabase/client";
 
type WsChannel = "experiments" | "scrapers" | "notifications" | "metrics";
 
interface UseWebSocketOptions<T> {
  channel: WsChannel;
  onMessage: (data: T) => void;
}
 
/**
 * Connects to FastAPI WebSocket at /ws/{channel}?token={jwt}.
 * Automatically reconnects on close/error with exponential backoff.
 * The JWT is fetched from the active Supabase session.
 */
export function useWebSocket<T>({ channel, onMessage }: UseWebSocketOptions<T>) {
  const wsRef  = useRef<WebSocket | null>(null);
  const supabase = createBrowserClient();
  const [status, setStatus] = useState<"connecting"|"open"|"closed">("connecting");
  const retryDelay = useRef(1000);
 
  const connect = useCallback(async () => {
    const { data } = await supabase.auth.getSession();
    const token = data.session?.access_token;
    if (!token) return;
    const base = process.env.NEXT_PUBLIC_API_URL!.replace(/^https?/, "wss");
    const ws = new WebSocket(`${base}/ws/${channel}?token=${token}`);
    wsRef.current = ws;
    ws.onopen    = () => { setStatus("open"); retryDelay.current = 1000; };
    ws.onmessage = (e) => onMessage(JSON.parse(e.data) as T);
    ws.onclose   = () => {
      setStatus("closed");
      setTimeout(() => { retryDelay.current = Math.min(retryDelay.current * 2, 30000); connect(); },
        retryDelay.current);
    };
    ws.onerror = () => ws.close();
  }, [channel, supabase, onMessage]);
 
  useEffect(() => { connect(); return () => wsRef.current?.close(); }, [connect]);
  return { status };
}
