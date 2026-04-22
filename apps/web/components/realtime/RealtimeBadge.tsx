"use client";
import React from "react";
import { motion } from "framer-motion";

interface RealtimeBadgeProps {
  active: boolean;
  label?: string;
}

/**
 * A small pulsating badge for real-time table indicators.
 */
export const RealtimeBadge: React.FC<RealtimeBadgeProps> = ({ active, label = "Real-time" }) => {
  return (
    <div className="flex items-center gap-1.5 bg-black/20 px-2 py-0.5 rounded border border-white/5">
      <div className="relative flex h-2 w-2">
        {active && (
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
        )}
        <span className={`relative inline-flex rounded-full h-2 w-2 ${active ? 'bg-blue-500' : 'bg-gray-500'}`}></span>
      </div>
      <span className="text-[10px] font-semibold text-gray-400 uppercase tracking-tight">
        {label}
      </span>
    </div>
  );
};
