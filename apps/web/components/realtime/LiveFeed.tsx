"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useWebSocket } from "@/hooks/useWebSocket";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Terminal, Activity, Zap } from "lucide-react";

interface FeedItem {
  id: string;
  type: "scrape" | "experiment" | "notification";
  message: string;
  timestamp: string;
}

/**
 * Scrolling real-time platform activity feed.
 * Connects to 'metrics' or 'notifications' WS channels.
 */
export function LiveFeed() {
  const [items, setItems] = useState<FeedItem[]>([]);

  // Listen to 'notifications' for feed updates
  useWebSocket<any>({
    channel: "notifications",
    onMessage: (data) => {
      const newItem: FeedItem = {
        id: Math.random().toString(36).substr(2, 9),
        type: data.type || "notification",
        message: data.body || data.message || "Platform update",
        timestamp: new Date().toLocaleTimeString(),
      };
      setItems((prev) => [newItem, ...prev].slice(0, 50));
    },
  });

  return (
    <div className="bg-card border rounded-lg overflow-hidden flex flex-col h-[400px]">
      <div className="p-3 border-b bg-muted/30 flex items-center justify-between">
        <h3 className="text-sm font-bold flex items-center gap-2">
          <Terminal className="h-4 w-4 text-primary" />
          Real-time Event Stream
        </h3>
        <Badge
          variant="outline"
          className="text-[10px] uppercase animate-pulse border-emerald-500/50 text-emerald-500"
        >
          Live
        </Badge>
      </div>

      <ScrollArea className="flex-1 p-4 font-mono text-[12px]">
        <AnimatePresence initial={false}>
          {items.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-muted-foreground opacity-50 space-y-2">
              <Activity className="h-8 w-8 animate-pulse" />
              <p>Waiting for events...</p>
            </div>
          ) : (
            <div className="space-y-3">
              {items.map((item) => (
                <motion.div
                  key={item.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="flex gap-3 border-b border-muted pb-2 last:border-0"
                >
                  <span className="text-muted-foreground shrink-0">
                    [{item.timestamp}]
                  </span>
                  <div className="flex flex-col gap-1">
                    <span className="font-bold flex items-center gap-1">
                      <Zap className="h-3 w-3 text-yellow-500" />
                      {item.type.toUpperCase()}
                    </span>
                    <span className="text-foreground/80 leading-relaxed">
                      {item.message}
                    </span>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </AnimatePresence>
      </ScrollArea>
    </div>
  );
}
