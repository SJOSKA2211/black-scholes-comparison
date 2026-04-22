"use client";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import React from "react";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "outline" | "ghost" | "danger";
  size?: "sm" | "md" | "lg";
}

export function Button({ className, variant = "primary", size = "md", ...props }: ButtonProps) {
  const variantStyles = {
    primary: "bg-blue-600 text-white hover:bg-blue-700 shadow-lg shadow-blue-900/20",
    secondary: "bg-slate-800 text-slate-100 hover:bg-slate-700 border border-slate-700",
    outline: "border border-slate-700 text-slate-300 hover:bg-slate-800 hover:text-white",
    ghost: "text-slate-400 hover:text-white hover:bg-slate-800",
    danger: "bg-red-600 text-white hover:bg-red-700 shadow-lg shadow-red-900/20"
  };

  const sizeStyles = {
    sm: "px-3 py-1.5 text-xs",
    md: "px-4 py-2 text-sm",
    lg: "px-6 py-3 text-base"
  };

  return (
    <motion.button
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      className={cn(
        "inline-flex items-center justify-center rounded-xl font-semibold transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed",
        variantStyles[variant],
        sizeStyles[size],
        className
      )}
      {...(props as any)}
    />
  );
}

export default Button;
