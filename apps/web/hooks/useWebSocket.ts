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
 */
export function useWebSocket<T>({ channel, onMessage }: UseWebSocketOptions<T>) {
  const wsRef = useRef<WebSocket | null>(null);
  const supabase = createBrowserClient();
  const [status, setStatus] = useState<"connecting" | "open" | "closed">("connecting");
  const retryDelay = useRef(1000);

  const connect = useCallback(async () => {
    const { data } = await supabase.auth.getSession();
    const token = data.session?.access_token;
    if (!token) return;

    // Build WebSocket URL
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const base = apiUrl.replace(/^http/, "ws");
    const ws = new WebSocket(`${base}/ws/${channel}?token=${token}`);
    
    wsRef.current = ws;

    ws.onopen = () => {
      console.log(`WebSocket connected to ${channel}`);
      setStatus("open");
      retryDelay.current = 1000;
    };

    ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        onMessage(data as T);
      } catch (err) {
        console.error("WebSocket message parse error", err);
      }
    };

    ws.onclose = () => {
      console.log(`WebSocket disconnected from ${channel}`);
      setStatus("closed");
      // Reconnect with exponential backoff
      setTimeout(() => {
        retryDelay.current = Math.min(retryDelay.current * 2, 30000);
        connect();
      }, retryDelay.current);
    };

    ws.onerror = (err) => {
      console.error(`WebSocket error on ${channel}`, err);
      ws.close();
    };
  }, [channel, supabase.auth, onMessage]);

  useEffect(() => {
    connect();
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  return { status };
}
