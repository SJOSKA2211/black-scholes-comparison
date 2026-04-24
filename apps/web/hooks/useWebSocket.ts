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
export function useWebSocket<T>({
  channel,
  onMessage,
}: UseWebSocketOptions<T>) {
  const wsRef = useRef<WebSocket | null>(null);
  const supabase = createBrowserClient();
  const [status, setStatus] = useState<"connecting" | "open" | "closed">(
    "connecting",
  );
  const retryDelay = useRef(1000);
  const onMessageRef = useRef(onMessage);

  useEffect(() => {
    onMessageRef.current = onMessage;
  }, [onMessage]);

  const connect = useCallback(
    async function connectImpl() {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const base = apiUrl.replace(/^http/, "ws");
      const ws = new WebSocket(`${base}/ws/${channel}`);

      wsRef.current = ws;

      ws.onopen = () => {
        setStatus("open");
        retryDelay.current = 1000;
      };

      ws.onmessage = (event) => {
        try {
          const parsedData = JSON.parse(event.data);
          onMessageRef.current(parsedData as T);
        } catch (error) {
          console.error("WebSocket message parsing failed", error);
        }
      };

      ws.onclose = () => {
        setStatus("closed");
        setTimeout(() => {
          retryDelay.current = Math.min(retryDelay.current * 2, 30000);
          void connectImpl();
        }, retryDelay.current);
      };

      ws.onerror = () => ws.close();
    },
    [channel, supabase],
  );

  useEffect(() => {
    connect();
    return () => wsRef.current?.close();
  }, [connect]);

  return { status };
}
