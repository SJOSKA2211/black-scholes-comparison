"use client";

import React, { useState } from "react";
import { useRealtime } from "@/hooks/useRealtime";
import { motion, AnimatePresence } from "framer-motion";
import { Database, Clock, ArrowRight, CheckCircle2 } from "lucide-react";

interface ScrapeRun {
  id: string;
  market: string;
  scraper_class: string;
  status: string;
  rows_scraped: number;
  finished_at: string;
}

export function LiveFeed() {
  const [runs, setRuns] = useState<ScrapeRun[]>([]);

  useRealtime<ScrapeRun>({
    table: "scrape_runs",
    onData: (newRun) => {
      setRuns((prev) => [newRun, ...prev].slice(0, 10));
    },
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider flex items-center gap-2">
          <Database className="w-4 h-4 text-blue-500" />
          Ingestion Feed
        </h3>
        <span className="flex h-2 w-2 rounded-full bg-blue-500 animate-pulse" />
      </div>

      <div className="space-y-3">
        <AnimatePresence initial={false}>
          {runs.length === 0 ? (
            <div className="text-center py-8 text-slate-600 text-xs italic">
              Waiting for ingestion events...
            </div>
          ) : (
            runs.map((run) => (
              <motion.div
                key={run.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="glass-card p-3 flex items-center justify-between group"
              >
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-lg ${
                    run.status === "success" ? "bg-emerald-500/10 text-emerald-500" : "bg-blue-500/10 text-blue-500"
                  }`}>
                    <CheckCircle2 className="w-4 h-4" />
                  </div>
                  <div>
                    <p className="text-xs font-bold text-white uppercase tracking-tighter">
                      {run.market} · {run.scraper_class.replace("Scraper", "")}
                    </p>
                    <div className="flex items-center gap-2 text-[10px] text-slate-500">
                      <Clock className="w-3 h-3" />
                      {new Date(run.finished_at || Date.now()).toLocaleTimeString()}
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-xs font-black text-white">+{run.rows_scraped}</p>
                  <p className="text-[9px] font-bold text-slate-600 uppercase tracking-widest">Rows</p>
                </div>
              </motion.div>
            ))
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
