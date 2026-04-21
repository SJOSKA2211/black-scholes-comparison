"use client";
import React from "react";
import { Bell, User, Search } from "lucide-react";
import { useNotifications } from "@/hooks/useNotifications";
import { motion, AnimatePresence } from "framer-motion";

export function Header() {
  const { unreadCount } = useNotifications();

  return (
    <header className="h-16 border-b border-slate-800 flex items-center justify-between px-8 bg-slate-950/50 backdrop-blur-md sticky top-0 z-10">
      <div className="flex items-center flex-1">
        <div className="relative w-96 max-w-full">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
          <input 
            type="text" 
            placeholder="Search experiments..." 
            className="w-full bg-slate-900 border border-slate-800 rounded-full py-1.5 pl-10 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all"
          />
        </div>
      </div>

      <div className="flex items-center space-x-4">
        <div className="relative">
          <button className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-full transition-all">
            <Bell className="h-5 w-5" />
            <AnimatePresence>
              {unreadCount > 0 && (
                <motion.span 
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  exit={{ scale: 0 }}
                  className="absolute top-1.5 right-1.5 h-4 w-4 bg-red-500 text-[10px] font-bold text-white flex items-center justify-center rounded-full border-2 border-slate-950"
                >
                  {unreadCount}
                </motion.span>
              )}
            </AnimatePresence>
          </button>
        </div>

        <div className="h-8 w-px bg-slate-800" />

        <button className="flex items-center space-x-3 p-1.5 rounded-full hover:bg-slate-800 transition-all border border-transparent hover:border-slate-700">
          <div className="h-8 w-8 rounded-full bg-gradient-to-br from-blue-500 to-emerald-500 flex items-center justify-center">
            <User className="h-5 w-5 text-white" />
          </div>
          <div className="hidden md:block text-left">
            <p className="text-sm font-medium text-white leading-none">Researcher</p>
            <p className="text-xs text-slate-500 mt-1">MATH499 Senior</p>
          </div>
        </button>
      </div>
    </header>
  );
}
