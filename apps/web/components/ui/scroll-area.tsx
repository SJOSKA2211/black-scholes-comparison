"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

type ScrollAreaProps = React.HTMLAttributes<HTMLDivElement>;

/**
 * Custom ScrollArea component to satisfy Shadcn-like imports.
 * Uses standard CSS for scrolling with a clean look.
 */
export function ScrollArea({ className, children, ...props }: ScrollAreaProps) {
  return (
    <div
      className={cn("relative overflow-hidden", className)}
      {...props}
    >
      <div className="h-full w-full overflow-auto scrollbar-thin scrollbar-thumb-slate-800 scrollbar-track-transparent">
        {children}
      </div>
    </div>
  );
}

export default ScrollArea;
