"use client";

import { useEffect, useRef, useCallback, useState } from "react";
import { createBrowserClient } from "@/lib/supabase/client";

type WsChannel = "experiments" | "scrapers" | "notifications" | "metrics";

interface UseWebSocketOptions<T> {
  channel: WsChannel;
  onMessage: (data: T) => void;
}

const supabase = createBrowserClient();

/**
 * Connects to FastAPI WebSocket at /ws/{channel}?token={jwt}.
 * Automatically reconnects on close/error with exponential backoff.
 */
export function useWebSocket<T>({ channel, onMessage }: UseWebSocketOptions<T>) {
  const wsRef = useRef<WebSocket | null>(null);
  const [status, setStatus] = useState<"connecting" | "open" | "closed">("connecting");
  const retryDelay = useRef(1000);
  const onMessageRef = useRef(onMessage);

  useEffect(() => {
    onMessageRef.current = onMessage;
  }, [onMessage]);

  const connect = useCallback(async () => {
    try {
      const { data } = await supabase.auth.getSession();
      const token = data.session?.access_token;
      if (!token) return;

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const base = apiUrl.replace(/^http/, "ws");
      const ws = new WebSocket(`${base}/ws/${channel}?token=${token}`);

      wsRef.current = ws;

      ws.onopen = () => {
        setStatus("open");
        retryDelay.current = 1000;
      };

      ws.onmessage = (e) => {
        try {
          const parsed = JSON.parse(e.data);
          onMessageRef.current(parsed as T);
        } catch (err) {
          console.error("WS Parse Error", err);
        }
      };

      ws.onclose = () => {
        setStatus("closed");
        // Reconnect via a separate trigger to avoid circular dependency
        const timer = setTimeout(() => {
          retryDelay.current = Math.min(retryDelay.current * 2, 30000);
          // Use a flag or ref to trigger reconnect
          setReconnectTrigger(prev => prev + 1);
        }, retryDelay.current);
        return () => clearTimeout(timer);
      };

      ws.onerror = () => ws.close();
    } catch (err) {
      console.error("WS Connect Error", err);
      setStatus("closed");
    }
  }, [channel]);

  const [reconnectTrigger, setReconnectTrigger] = useState(0);

  useEffect(() => {
    connect();
    return () => {
      wsRef.current?.close();
    };
  }, [connect, reconnectTrigger]);

  return { status };
}
