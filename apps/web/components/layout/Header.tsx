"use client";
import NotificationBell from "./NotificationBell";
import ConnectionStatus from "./ConnectionStatus";
import { User } from "@supabase/supabase-js";

export function Header({ user }: { user: User }) {
  return (
    <header className="flex h-16 items-center justify-between border-b border-slate-800 bg-slate-900/30 px-8">
      <div className="flex items-center gap-6">
        <h2 className="text-lg font-semibold text-white">Dashboard</h2>
        <ConnectionStatus />
      </div>
      <div className="flex items-center gap-4">
        <NotificationBell />
        <div className="h-4 w-px bg-slate-800" />
        <div className="flex items-center gap-3">
          <div className="text-right">
            <p className="text-sm font-medium text-white">
              {user.email?.split("@")[0] || "Researcher"}
            </p>
            <p className="text-[10px] text-slate-500 uppercase tracking-widest">
              Researcher Mode
            </p>
          </div>
          <div className="h-8 w-8 rounded-full bg-blue-500/20 border border-blue-500/50 flex items-center justify-center">
            <span className="text-[10px] font-bold text-blue-400">RES</span>
          </div>
        </div>
      </div>
    </header>
  );
}

export default Header;
