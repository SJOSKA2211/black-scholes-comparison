"use client";
import { motion } from "framer-motion";
import { Zap, Activity, Target, History } from "lucide-react";
import { useExperiments } from "@/hooks/useExperiments";
import { useMarketData } from "@/hooks/useMarketData";
import { useHealth } from "@/hooks/useHealth";

import { LiveFeed } from "@/components/realtime/LiveFeed";

const container = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.1 } },
};

const item = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 },
};

export default function DashboardPage() {
  const { experiments, total: totalExperiments } = useExperiments();
  const { data: marketData } = useMarketData({ source: "spy" });
  const { data: health } = useHealth();

  const stats = [
    {
      name: "Total Experiments",
      value: totalExperiments?.toLocaleString() ?? experiments.length.toString(),
      icon: Zap,
      color: "text-yellow-500",
    },
    {
      name: "Active Market Feed",
      value: marketData?.[0]?.data_source?.toUpperCase() || "SPY / NSE",
      icon: Activity,
      color: "text-green-500",
    },
    {
      name: "Avg Precision",
      value: "99.99%",
      icon: Target,
      color: "text-blue-500",
    },
    {
      name: "System Health",
      value: health?.status === "ok" ? "Healthy" : "Degraded",
      icon: History,
      color: health?.status === "ok" ? "text-green-500" : "text-red-500",
    },
  ];

  return (
    <motion.div
      variants={container}
      initial="hidden"
      animate="visible"
      className="space-y-8"
    >
      {/* KPI Cards */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <motion.div
            key={stat.name}
            variants={item}
            className="glass-card p-6 shadow-sm group hover:border-blue-500/30 transition-all"
          >
            <div className="flex items-center gap-4">
              <div className={`rounded-xl bg-slate-800 p-2.5 ${stat.color} group-hover:scale-110 transition-transform`}>
                <stat.icon className="h-5 w-5" />
              </div>
              <div>
                <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">
                  {stat.name}
                </p>
                <p className="text-2xl font-black text-white font-outfit">{stat.value}</p>
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Recent Experiments (Realtime) */}
        <motion.div
          variants={item}
          className="lg:col-span-2 glass-card p-6 shadow-sm"
        >
          <div className="mb-6 flex items-center justify-between">
            <h3 className="text-lg font-bold text-white font-outfit">
              Live Research Activity
            </h3>
            <div className="flex items-center gap-2">
              <span className="flex h-2 w-2 rounded-full bg-blue-500 animate-pulse" />
              <span className="text-[10px] font-bold text-blue-500 uppercase tracking-widest">
                Realtime Feed
              </span>
            </div>
          </div>
          <div className="space-y-3">
            {experiments.length === 0 ? (
               <div className="h-64 flex flex-col items-center justify-center text-slate-600">
                 <Zap className="w-12 h-12 mb-2 opacity-10" />
                 <p className="text-sm">No research activity recorded yet</p>
               </div>
            ) : (
              experiments.slice(0, 6).map((exp) => (
                <div
                  key={exp.id}
                  className="flex items-center justify-between rounded-xl border border-white/5 bg-white/5 p-4 transition-all hover:bg-white/10 hover:border-white/10 group"
                >
                  <div className="flex items-center gap-4">
                    <div className="h-10 w-10 rounded-lg bg-slate-900 flex items-center justify-center font-mono text-xs font-bold text-blue-500 border border-slate-700 group-hover:border-blue-500/50 transition-all">
                      {exp.method_type.substring(0, 2).toUpperCase()}
                    </div>
                    <div>
                      <p className="text-sm font-bold text-slate-200 capitalize">
                        {exp.method_type.replace(/_/g, " ")}
                      </p>
                      <p className="text-[10px] text-slate-500 font-medium">
                        Price: <span className="text-white font-bold">{exp.computed_price.toFixed(4)}</span> · Latency: <span className="text-slate-400">{(exp.exec_seconds * 1000).toFixed(1)}ms</span>
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-[10px] font-mono text-slate-500 font-bold">
                      S:{exp.option_parameters.underlying_price} K:{exp.option_parameters.strike_price}
                    </p>
                    <p className="text-[9px] text-slate-600 font-bold uppercase tracking-tighter">
                      {new Date(exp.run_at).toLocaleTimeString()}
                    </p>
                  </div>
                </div>
              ))
            )}
          </div>
        </motion.div>

        {/* Market Status & Live Feed */}
        <motion.div
          variants={item}
          className="space-y-6"
        >
          <div className="glass-card p-6 shadow-sm">
            <h3 className="mb-6 text-lg font-bold text-white font-outfit">
              Market Ingestion
            </h3>
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="h-2 w-2 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.5)]" />
                  <span className="text-sm font-medium text-slate-300">
                    SPY (Yahoo Finance)
                  </span>
                </div>
                <span className="text-[10px] font-bold text-slate-500 uppercase">Live</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="h-2 w-2 rounded-full bg-orange-500 shadow-[0_0_8px_rgba(249,115,22,0.5)]" />
                  <span className="text-sm font-medium text-slate-300">
                    NSE (NIFTY 50)
                  </span>
                </div>
                <span className="text-[10px] font-bold text-slate-500 uppercase">
                  Delayed
                </span>
              </div>
              <div className="pt-6 border-t border-white/5">
                <div className="flex justify-between text-[10px] font-bold uppercase tracking-widest mb-4">
                  <span className="text-slate-500">Pipeline Status</span>
                  <span className="text-emerald-500">Optimal</span>
                </div>
                <div className="w-full bg-slate-800 h-1 rounded-full overflow-hidden">
                  <motion.div 
                    initial={{ width: 0 }}
                    animate={{ width: "94%" }}
                    className="bg-blue-600 h-full"
                  />
                </div>
              </div>
            </div>
          </div>

          <LiveFeed />
        </motion.div>
      </div>
    </motion.div>
  );
}
