"use client";

import { Bell, Search, Command, User, LogOut, ExternalLink } from "lucide-react";
import { motion } from "framer-motion";
import { ConnectionStatus } from "@/components/layout/ConnectionStatus";

export function Header() {
  return (
    <header className="h-20 border-b border-white/5 bg-slate-950/20 backdrop-blur-md px-8 flex items-center justify-between sticky top-0 z-40">
      <div className="flex items-center gap-6 flex-1">
        <div className="relative group max-w-md w-full">
           <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500 group-focus-within:text-indigo-400 transition-colors" />
           <input 
             type="text" 
             placeholder="Search experiments, methods, or market data..."
             className="w-full h-11 bg-slate-900/50 border border-white/5 rounded-xl pl-11 pr-16 focus:ring-2 focus:ring-indigo-500/30 outline-none transition-all placeholder:text-slate-600 text-sm"
           />
           <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-1 px-1.5 py-1 rounded bg-slate-800 border border-white/10">
              <Command className="w-3 h-3 text-slate-500" />
              <span className="text-[10px] font-bold text-slate-500">K</span>
           </div>
        </div>
      </div>

      <div className="flex items-center gap-6">
        <ConnectionStatus />
        
        <div className="h-6 w-px bg-white/10" />

        <div className="flex items-center gap-4">
          <motion.button 
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="relative w-10 h-10 rounded-xl bg-slate-900 border border-white/5 flex items-center justify-center text-slate-400 hover:text-white transition-colors"
          >
            <Bell className="w-5 h-5" />
            <span className="absolute top-2 right-2 w-2 h-2 bg-indigo-500 rounded-full border-2 border-slate-950" />
          </motion.button>

          <div className="flex items-center gap-3 pl-2 group cursor-pointer">
             <div className="text-right hidden sm:block">
                <p className="text-sm font-bold text-white leading-tight group-hover:text-indigo-400 transition-colors">Joseph Kamau</p>
                <p className="text-[10px] font-medium text-slate-500 uppercase tracking-wider">Lead Researcher</p>
             </div>
             <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 p-px">
                <div className="w-full h-full rounded-[11px] bg-slate-950 flex items-center justify-center overflow-hidden border border-white/10">
                   <User className="w-5 h-5 text-slate-400" />
                </div>
             </div>
          </div>
        </div>
      </div>
    </header>
  );
}
