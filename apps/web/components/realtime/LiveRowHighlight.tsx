"use client";

import React, { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

interface LiveRowHighlightProps {
  id: string | number;
  trigger: any;
  children: React.ReactNode;
  className?: string;
}

/**
 * Wraps a table row and provides a visual highlight animation
 * whenever the 'trigger' value changes (e.g. from a real-time update).
 */
export function LiveRowHighlight({
  id,
  trigger,
  children,
  className = "",
}: LiveRowHighlightProps) {
  const [isHighlighted, setIsHighlighted] = useState(false);

  useEffect(() => {
    if (trigger) {
      setIsHighlighted(true);
      const timer = setTimeout(() => setIsHighlighted(false), 2000);
      return () => clearTimeout(timer);
    }
  }, [trigger, id]);

  return (
    <tr
      className={`relative transition-colors duration-500 ${
        isHighlighted ? "bg-emerald-500/10" : ""
      } ${className}`}
    >
      <AnimatePresence>
        {isHighlighted && (
          <motion.div
            initial={{ opacity: 0, scaleX: 0 }}
            animate={{ opacity: 1, scaleX: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 border-l-2 border-emerald-500 pointer-events-none origin-left"
          />
        )}
      </AnimatePresence>
      {children}
    </tr>
  );
}
