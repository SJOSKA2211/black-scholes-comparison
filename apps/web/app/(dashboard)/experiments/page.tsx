"use client";

import { motion } from "framer-motion";
import { FlaskConical, Play, Save, History, BarChart2, Zap, Settings2 } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function ExperimentsPage() {
  return (
    <div className="space-y-10">
      <header className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <h1 className="text-4xl font-bold font-display tracking-tight text-white mb-2 flex items-center gap-3">
            <FlaskConical className="w-8 h-8 text-purple-400" />
            Grid Experiments
          </h1>
          <p className="text-slate-400 max-w-xl">
            Execute large-scale stability analysis by varying parameters across thousands of data points.
          </p>
        </div>
        <Button className="h-12 px-8 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-bold flex items-center gap-2 glow-purple transition-all active:scale-95 shadow-lg shadow-purple-600/20">
          <Play className="w-4 h-4 fill-current" /> New Experiment
        </Button>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Active Runs */}
        <div className="lg:col-span-2 space-y-6">
           <div className="glass-card p-8 rounded-3xl">
              <div className="flex items-center justify-between mb-8">
                 <h3 className="text-xl font-bold text-white flex items-center gap-2">
                    <Zap className="w-5 h-5 text-amber-400" />
                    Active Pipeline
                 </h3>
                 <span className="px-3 py-1 rounded-full bg-amber-400/10 border border-amber-400/20 text-[10px] font-bold text-amber-400 uppercase tracking-wider animate-pulse">Running</span>
              </div>

              <div className="bg-slate-950/50 rounded-2xl p-6 border border-white/5 border-l-4 border-l-amber-500">
                 <div className="flex items-center justify-between mb-4">
                    <div>
                       <h4 className="text-lg font-bold text-white mb-1">Volatility Surface Mapping</h4>
                       <p className="text-xs text-slate-500 font-mono">ID: exp_842a_9k1</p>
                    </div>
                    <div className="text-right">
                       <p className="text-xl font-mono font-bold text-white">68.4%</p>
                       <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">Progress</p>
                    </div>
                 </div>
                 <div className="h-2 bg-slate-900 rounded-full overflow-hidden mb-6">
                    <motion.div 
                      initial={{ width: 0 }}
                      animate={{ width: "68.4%" }}
                      className="h-full bg-gradient-to-r from-amber-600 to-amber-400 rounded-full" 
                    />
                 </div>
                 <div className="flex items-center gap-4 text-xs">
                    <div className="flex items-center gap-1.5 text-slate-400">
                       <BarChart2 className="w-3.5 h-3.5" /> 8,240 / 12,048 points
                    </div>
                    <div className="flex items-center gap-1.5 text-slate-400">
                       <Settings2 className="w-3.5 h-3.5" /> Grid: 50x50x5
                    </div>
                 </div>
              </div>
           </div>

           <div className="glass-card p-8 rounded-3xl">
              <div className="flex items-center justify-between mb-8">
                 <h3 className="text-xl font-bold text-white">Historical Stability Benchmarks</h3>
                 <Button variant="ghost" className="text-xs text-indigo-400 hover:bg-indigo-400/10">Compare Sets</Button>
              </div>
              <div className="space-y-4">
                 {[
                   { name: "FDM CFL Limit Boundary", date: "Apr 20, 2026", stability: "98.2%", method: "Explicit FDM" },
                   { name: "MC Convergence Rate", date: "Apr 18, 2026", stability: "99.9%", method: "Standard MC" },
                   { name: "Binomial Tree Oscillation", date: "Apr 15, 2026", stability: "94.5%", method: "CRR Binomial" },
                 ].map((exp, i) => (
                   <div key={i} className="flex items-center justify-between p-4 rounded-2xl hover:bg-white/5 transition-colors group cursor-pointer border border-transparent hover:border-white/5">
                      <div className="flex items-center gap-4">
                         <div className="w-10 h-10 rounded-xl bg-slate-900 flex items-center justify-center border border-white/5 text-slate-500 group-hover:text-indigo-400 transition-colors">
                            <Save className="w-5 h-5" />
                         </div>
                         <div>
                            <p className="text-sm font-bold text-white group-hover:text-indigo-400 transition-colors">{exp.name}</p>
                            <p className="text-xs text-slate-500">{exp.date} · {exp.method}</p>
                         </div>
                      </div>
                      <div className="text-right">
                         <p className="text-sm font-mono font-bold text-emerald-400">{exp.stability}</p>
                         <p className="text-[10px] text-slate-600 font-bold uppercase tracking-tighter">Finite Agreement</p>
                      </div>
                   </div>
                 ))}
              </div>
           </div>
        </div>

        {/* Configuration Column */}
        <div className="space-y-6">
           <div className="glass-card p-8 rounded-3xl">
              <h3 className="text-sm font-bold text-slate-400 uppercase tracking-widest mb-6">Quick Presets</h3>
              <div className="space-y-3">
                 {["Stress Test (σ=0.8)", "Low Yield Environment", "Vol Smile Inversion", "Long Term Convergence"].map((preset) => (
                   <button key={preset} className="w-full p-4 rounded-2xl bg-slate-950/50 border border-white/5 text-left text-sm font-medium text-slate-300 hover:text-white hover:border-indigo-500/30 hover:bg-indigo-500/5 transition-all">
                      {preset}
                   </button>
                 ))}
              </div>
           </div>

           <div className="glass-card p-8 rounded-3xl bg-purple-600/5 border border-purple-500/10">
              <h4 className="font-bold text-white mb-4">Queue Capacity</h4>
              <div className="space-y-4">
                 <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-500">RabbitMQ Workers</span>
                    <span className="text-slate-300 font-bold">4 / 8 Active</span>
                 </div>
                 <div className="h-1.5 bg-slate-900 rounded-full overflow-hidden">
                    <div className="h-full bg-purple-500 w-1/2" />
                 </div>
                 <p className="text-[10px] text-slate-500 leading-relaxed italic">
                   Async processing allows background grid computation without blocking the main research portal.
                 </p>
              </div>
           </div>
        </div>
      </div>
    </div>
  );
}
