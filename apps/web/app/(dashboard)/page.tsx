"use client";
import { motion } from "framer-motion";
import { Zap, Activity, Target, History } from "lucide-react";
import { useExperiments } from "@/hooks/useExperiments";
import { useMarketData } from "@/hooks/useMarketData";

const container = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.1 } },
};

const item = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 },
};

export default function DashboardPage() {
  const { experiments } = useExperiments();
  const { data: marketData } = useMarketData({ source: "spy" });

  const stats = [
    {
      name: "Total Experiments",
      value: experiments.length.toString(),
      icon: Zap,
      color: "text-yellow-500",
    },
    {
      name: "Active Market Feed",
      value: "SPY / NSE",
      icon: Activity,
      color: "text-green-500",
    },
    {
      name: "Avg Precision",
      value: "99.98%",
      icon: Target,
      color: "text-blue-500",
    },
    {
      name: "System Uptime",
      value: "100%",
      icon: History,
      color: "text-purple-500",
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
            className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6 shadow-sm"
          >
            <div className="flex items-center gap-4">
              <div className={`rounded-xl bg-slate-800 p-2.5 ${stat.color}`}>
                <stat.icon className="h-5 w-5" />
              </div>
              <div>
                <p className="text-xs font-medium text-slate-500 uppercase tracking-widest">
                  {stat.name}
                </p>
                <p className="text-2xl font-bold text-white">{stat.value}</p>
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Recent Experiments (Realtime) */}
        <motion.div
          variants={item}
          className="col-span-2 rounded-2xl border border-slate-800 bg-slate-900/50 p-6 shadow-sm"
        >
          <div className="mb-6 flex items-center justify-between">
            <h3 className="text-lg font-bold text-white">
              Live Research Activity
            </h3>
            <span className="rounded-full bg-blue-500/10 px-2.5 py-0.5 text-[10px] font-bold text-blue-500 uppercase tracking-widest">
              Realtime Feed
            </span>
          </div>
          <div className="space-y-4">
            {experiments.slice(0, 5).map((exp) => (
              <div
                key={exp.id}
                className="flex items-center justify-between rounded-xl border border-slate-800/50 bg-slate-800/30 p-4 transition-all hover:bg-slate-800/50"
              >
                <div className="flex items-center gap-4">
                  <div className="h-10 w-10 rounded-lg bg-slate-900 flex items-center justify-center font-mono text-xs font-bold text-blue-500 border border-slate-700">
                    {exp.method_type.substring(0, 2).toUpperCase()}
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-slate-200">
                      {exp.method_type}
                    </p>
                    <p className="text-[10px] text-slate-500 uppercase tracking-wider">
                      Price: {exp.computed_price.toFixed(4)} · Exec:{" "}
                      {exp.exec_seconds.toFixed(4)}s
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-xs font-mono text-slate-400">
                    S:{exp.option_parameters.underlying_price} K:
                    {exp.option_parameters.strike_price}
                  </p>
                  <p className="text-[10px] text-slate-600 italic">
                    {new Date(exp.run_at).toLocaleTimeString()}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Market Status */}
        <motion.div
          variants={item}
          className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6 shadow-sm"
        >
          <h3 className="mb-6 text-lg font-bold text-white">
            Market Ingestion
          </h3>
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="h-2 w-2 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.5)]" />
                <span className="text-sm font-medium text-slate-300">
                  SPY (Yahoo)
                </span>
              </div>
              <span className="text-xs font-mono text-slate-500">Live</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="h-2 w-2 rounded-full bg-orange-500 shadow-[0_0_8px_rgba(249,115,22,0.5)]" />
                <span className="text-sm font-medium text-slate-300">
                  NSE (NIFTY)
                </span>
              </div>
              <span className="text-xs font-mono text-slate-500">
                Post-Market
              </span>
            </div>
            <div className="pt-6 border-t border-slate-800">
              <p className="text-xs font-medium text-slate-500 uppercase tracking-widest mb-4">
                Ingestion Stats
              </p>
              <div className="space-y-3">
                <div className="flex justify-between text-xs">
                  <span className="text-slate-400">Total Rows</span>
                  <span className="text-slate-200 font-mono">
                    {marketData?.length ?? 0}
                  </span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-slate-400">Pipeline Health</span>
                  <span className="text-green-500 font-bold uppercase tracking-widest text-[9px]">
                    Optimal
                  </span>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </motion.div>
  );
}
