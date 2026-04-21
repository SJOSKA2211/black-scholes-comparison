"use client";
import { useAuth } from "@/hooks/useAuth";
import NotificationBell from "./NotificationBell";
import ConnectionStatus from "./ConnectionStatus";
import { User } from "@supabase/supabase-js";

export default function Header({ user }: { user: User }) {
  const { signOut } = useAuth();

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
            <p className="text-sm font-medium text-white">{user.email?.split("@")[0]}</p>
            <p className="text-[10px] text-slate-500 uppercase tracking-widest">Researcher</p>
          </div>
          <button 
            onClick={signOut}
            className="h-8 w-8 rounded-full bg-slate-800 flex items-center justify-center hover:bg-slate-700 transition-colors"
          >
            <span className="text-xs">LOG</span>
          </button>
        </div>
      </div>
    </header>
  );
}
