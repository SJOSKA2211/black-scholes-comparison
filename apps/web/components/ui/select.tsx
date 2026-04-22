"use client";
import * as React from "react";
import { cn } from "@/lib/utils";
import { ChevronDown } from "lucide-react";

export function Select({ children, value }: any) {
  return (
    <div className="relative inline-block w-full">
      {React.Children.map(children, (child: any) => {
        if (child.type === SelectTrigger) {
          return React.cloneElement(child, { value });
        }
        return null;
      })}
    </div>
  );
}

export function SelectTrigger({ children, className }: any) {
  return (
    <div className={cn("flex h-10 w-full items-center justify-between rounded-md border border-slate-800 bg-slate-950 px-3 py-2 text-sm", className)}>
      {children}
      <ChevronDown className="h-4 w-4 opacity-50" />
    </div>
  );
}

export function SelectValue({ placeholder, value }: any) {
  return <span>{value || placeholder}</span>;
}

export function SelectContent() {
  return null; // Minimal implementation
}

export function SelectItem() {
  return null; // Minimal implementation
}
