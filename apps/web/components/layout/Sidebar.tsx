"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import { 
  LayoutDashboard, 
  Calculator, 
  FlaskConical, 
  ShieldCheck, 
  Globe2, 
  Layers,
  Settings,
  HelpCircle,
  ChevronRight
} from "lucide-react";

const menuItems = [
  { label: "Overview", icon: LayoutDashboard, href: "/" },
  { label: "Live Pricer", icon: Calculator, href: "/pricer" },
  { label: "Experiments", icon: FlaskConical, href: "/experiments" },
  { label: "Validation", icon: ShieldCheck, href: "/validation" },
  { label: "Market Scrapers", icon: Globe2, href: "/scrapers" },
  { label: "Methods Tree", icon: Layers, href: "/methods" },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-72 hidden lg:flex flex-col border-r border-white/5 bg-slate-950/50 backdrop-blur-3xl relative z-50">
      <div className="p-8">
        <div className="flex items-center gap-3 mb-10">
          <div className="w-10 h-10 bg-indigo-600 rounded-xl flex items-center justify-center glow-blue">
            <Layers className="w-6 h-6 text-white" />
          </div>
          <div>
             <h1 className="text-xl font-bold font-display tracking-tight text-white leading-none">Antigravity</h1>
             <p className="text-[10px] uppercase tracking-[0.2em] font-bold text-slate-500 mt-1">Research Lab</p>
          </div>
        </div>

        <nav className="space-y-1">
          {menuItems.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link key={item.label} href={item.href}>
                <div className={`group flex items-center justify-between px-4 py-3 rounded-xl transition-all duration-300 relative ${isActive ? 'bg-indigo-600/10 text-white' : 'text-slate-400 hover:text-slate-100 hover:bg-white/5'}`}>
                  <div className="flex items-center gap-3 relative z-10">
                    <item.icon className={`w-5 h-5 transition-colors ${isActive ? 'text-indigo-400' : 'group-hover:text-slate-200'}`} />
                    <span className="font-medium">{item.label}</span>
                  </div>
                  {isActive && (
                    <motion.div 
                      layoutId="sidebar-active"
                      className="absolute left-0 w-1 h-6 bg-indigo-500 rounded-r-full" 
                    />
                  )}
                  <ChevronRight className={`w-4 h-4 transition-all ${isActive ? 'opacity-100' : 'opacity-0 -translate-x-2 group-hover:opacity-40 group-hover:translate-x-0'}`} />
                </div>
              </Link>
            );
          })}
        </nav>
      </div>

      <div className="mt-auto p-8 border-t border-white/5">
        <div className="bg-gradient-to-br from-indigo-600/10 to-transparent p-4 rounded-2xl border border-indigo-500/10 mb-6">
           <p className="text-xs font-bold text-indigo-400 uppercase tracking-widest mb-1">Documentation</p>
           <p className="text-[11px] text-slate-500 leading-relaxed mb-3">Learn about the 12 numerical methods implemented.</p>
           <Link href="/docs" className="text-xs font-bold text-white flex items-center gap-1 hover:gap-2 transition-all">
             View Docs <ArrowRight className="w-3 h-3" />
           </Link>
        </div>

        <div className="flex flex-col gap-2">
           <button className="flex items-center gap-3 px-4 py-2 text-slate-400 hover:text-slate-100 transition-colors text-sm font-medium">
             <Settings className="w-4 h-4" /> Settings
           </button>
           <button className="flex items-center gap-3 px-4 py-2 text-slate-400 hover:text-slate-100 transition-colors text-sm font-medium">
             <HelpCircle className="w-4 h-4" /> Support
           </button>
        </div>
      </div>
    </aside>
  );
}

function ArrowRight({ className }: { className?: string }) {
  return <ChevronRight className={className} />;
}
