"use client";

import { motion } from "framer-motion";
import { TrendingUp, Activity, Database, Zap, ArrowUpRight, BarChart3 } from "lucide-react";

const stats = [
  { label: "Computations", value: "24,812", change: "+12%", icon: Zap, color: "text-indigo-400", bg: "bg-indigo-400/10" },
  { label: "Avg MAPE", value: "0.042%", change: "-0.005%", icon: TrendingUp, color: "text-emerald-400", bg: "bg-emerald-400/10" },
  { label: "Market Rows", value: "1.2M", change: "+143k", icon: Database, color: "text-cyan-400", bg: "bg-cyan-400/10" },
  { label: "System Health", value: "Optimal", change: "100%", icon: Activity, color: "text-amber-400", bg: "bg-amber-400/10" },
];

export default function DashboardOverview() {
  return (
    <div className="space-y-10">
      <header>
        <h1 className="text-4xl font-bold font-display tracking-tight text-white mb-2">Research Overview</h1>
        <p className="text-slate-400 max-w-2xl">
          Real-time tracking of numerical method convergence, market data ingestion, and platform health metrics.
        </p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, i) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className="glass-card p-6 rounded-3xl group cursor-pointer hover:border-white/10 transition-all duration-300"
          >
            <div className="flex items-center justify-between mb-4">
              <div className={`w-12 h-12 ${stat.bg} rounded-2xl flex items-center justify-center transition-transform group-hover:scale-110 duration-500`}>
                <stat.icon className={`w-6 h-6 ${stat.color}`} />
              </div>
              <div className="text-xs font-semibold px-2 py-1 rounded-full bg-slate-800 text-slate-300 flex items-center gap-1">
                {stat.change}
                <ArrowUpRight className="w-3 h-3" />
              </div>
            </div>
            <p className="text-sm font-medium text-slate-500 mb-1">{stat.label}</p>
            <h3 className="text-2xl font-bold text-white tracking-tight">{stat.value}</h3>
          </motion.div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 glass-card p-8 rounded-3xl min-h-[400px] flex flex-col">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h3 className="text-xl font-bold text-white">Convergence Velocity</h3>
              <p className="text-sm text-slate-500">Method agreement over parameter iterations</p>
            </div>
            <Button variant="ghost" className="text-xs text-indigo-400 hover:text-indigo-300 hover:bg-indigo-400/10">
              Export Analysis
            </Button>
          </div>
          <div className="flex-1 bg-slate-950/40 rounded-2xl border border-white/5 flex items-center justify-center relative overflow-hidden">
             <BarChart3 className="w-12 h-12 text-slate-800 animate-pulse" />
             <div className="absolute inset-0 bg-gradient-to-t from-indigo-500/5 to-transparent" />
          </div>
        </div>

        <div className="glass-card p-8 rounded-3xl flex flex-col">
           <h3 className="text-xl font-bold text-white mb-6">Recent Scrapes</h3>
           <div className="space-y-6 flex-1">
             {[
               { market: "SPY (NYSE)", rows: "1,240", status: "success", time: "2h ago" },
               { market: "NIFTY (NSE)", rows: "4,812", status: "partial", time: "5h ago" },
               { market: "VIX (CBOE)", rows: "842", status: "success", time: "12h ago" },
             ].map((scrape, i) => (
               <div key={i} className="flex items-center justify-between group">
                 <div className="flex items-center gap-4">
                   <div className={`w-2 h-2 rounded-full ${scrape.status === 'success' ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]' : 'bg-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.5)]'}`} />
                   <div>
                     <p className="text-sm font-semibold text-slate-200">{scrape.market}</p>
                     <p className="text-xs text-slate-500">{scrape.rows} rows ingested</p>
                   </div>
                 </div>
                 <span className="text-[10px] uppercase font-bold tracking-wider text-slate-600 group-hover:text-slate-400 transition-colors">{scrape.time}</span>
               </div>
             ))}
           </div>
           <Button className="w-full mt-8 bg-slate-800 hover:bg-slate-700 text-white rounded-xl border border-white/5 transition-all">
             View All Activity
           </Button>
        </div>
      </div>
    </div>
  );
}

function Button({ children, className, variant = "primary", ...props }: any) {
  return (
    <button className={`inline-flex items-center justify-center px-4 py-2 rounded-lg font-medium transition-all active:scale-95 ${className}`} {...props}>
      {children}
    </button>
  )
}
