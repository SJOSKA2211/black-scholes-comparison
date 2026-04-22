"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Calculator, Play, Download, Save, RefreshCcw } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function PricerPage() {
  const [loading, setLoading] = useState(false);

  return (
    <div className="space-y-10">
      <header className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <h1 className="text-4xl font-bold font-display tracking-tight text-white mb-2 flex items-center gap-3">
            <Calculator className="w-8 h-8 text-indigo-400" />
            Live Pricer
          </h1>
          <p className="text-slate-400 max-w-xl">
            Execute simultaneous comparisons across all 12 numerical implementations using custom boundary conditions.
          </p>
        </div>
        <div className="flex items-center gap-3">
           <Button variant="outline" className="h-11 px-6 rounded-xl border-white/5 bg-slate-900/50 text-slate-300 hover:text-white flex items-center gap-2">
             <Save className="w-4 h-4" /> Save Set
           </Button>
           <Button className="h-11 px-6 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white flex items-center gap-2 glow-blue transition-all active:scale-95 shadow-lg shadow-indigo-600/20">
             <Play className="w-4 h-4 fill-current" /> Compute All
           </Button>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        {/* Form Column */}
        <div className="lg:col-span-1 space-y-6">
           <div className="glass-card p-6 rounded-3xl space-y-6">
             <h3 className="text-sm font-bold text-slate-400 uppercase tracking-widest mb-4">Boundary Conditions</h3>
             
             {[
               { label: "Underlying (S)", value: 100, min: 1, max: 1000 },
               { label: "Strike (K)", value: 100, min: 1, max: 1000 },
               { label: "Maturity (T)", value: 1, min: 0.1, max: 10 },
               { label: "Volatility (σ)", value: 0.2, min: 0.01, max: 2 },
               { label: "Risk-Free (r)", value: 0.05, min: 0, max: 0.2 },
             ].map((param) => (
               <div key={param.label} className="space-y-3">
                 <div className="flex items-center justify-between">
                   <label className="text-xs font-semibold text-slate-300">{param.label}</label>
                   <span className="text-xs font-mono text-indigo-400">{param.value}</span>
                 </div>
                 <div className="h-1.5 bg-slate-950 rounded-full overflow-hidden border border-white/5">
                    <div className="h-full bg-indigo-500 rounded-full" style={{ width: '40%' }} />
                 </div>
               </div>
             ))}

             <div className="pt-4 space-y-4">
                <div className="flex items-center justify-between p-3 rounded-xl bg-slate-950/50 border border-white/5">
                   <span className="text-xs font-medium text-slate-400">Option Type</span>
                   <div className="flex bg-slate-900 p-1 rounded-lg">
                      <button className="px-3 py-1 rounded-md bg-indigo-600 text-[10px] font-bold text-white uppercase">Call</button>
                      <button className="px-3 py-1 rounded-md text-[10px] font-bold text-slate-500 uppercase hover:text-slate-300">Put</button>
                   </div>
                </div>
                <div className="flex items-center justify-between p-3 rounded-xl bg-slate-950/50 border border-white/5">
                   <span className="text-xs font-medium text-slate-400">Exercise Type</span>
                   <div className="flex bg-slate-900 p-1 rounded-lg">
                      <button className="px-3 py-1 rounded-md bg-slate-800 text-[10px] font-bold text-slate-400 uppercase">European</button>
                      <button className="px-3 py-1 rounded-md text-[10px] font-bold text-slate-500 uppercase">American</button>
                   </div>
                </div>
             </div>
           </div>
        </div>

        {/* Results Column */}
        <div className="lg:col-span-3 space-y-8">
           <div className="glass-card p-8 rounded-3xl h-[400px] flex flex-col">
              <div className="flex items-center justify-between mb-8">
                 <h3 className="text-xl font-bold text-white">Cross-Method Comparison</h3>
                 <div className="flex items-center gap-2">
                    <div className="flex items-center gap-1.5 px-2 py-1 rounded bg-emerald-500/10 border border-emerald-500/20">
                       <div className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                       <span className="text-[10px] font-bold text-emerald-400 uppercase">Analytical Match</span>
                    </div>
                 </div>
              </div>
              <div className="flex-1 bg-slate-950/40 rounded-2xl border border-white/5 flex items-center justify-center">
                 <p className="text-slate-600 font-medium italic">Execute computation to render method comparison chart...</p>
              </div>
           </div>

           <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
             {[
               { method: "Explicit FDM", price: "10.4502", error: "-0.004%", color: "border-l-indigo-500" },
               { method: "Standard MC", price: "10.4491", error: "+0.012%", color: "border-l-cyan-500" },
               { method: "Binomial CRR", price: "10.4508", error: "+0.002%", color: "border-l-emerald-500" },
             ].map((res, i) => (
               <motion.div
                 key={res.method}
                 initial={{ opacity: 0, x: -10 }}
                 animate={{ opacity: 1, x: 0 }}
                 transition={{ delay: i * 0.1 }}
                 className={`glass-card p-5 rounded-2xl border-l-4 ${res.color}`}
               >
                 <p className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-1">{res.method}</p>
                 <h4 className="text-2xl font-bold text-white mb-2">{res.price}</h4>
                 <div className="flex items-center gap-2">
                   <span className="text-[10px] font-bold text-emerald-400 bg-emerald-400/10 px-1.5 py-0.5 rounded uppercase">MAPE: {res.error}</span>
                   <span className="text-[10px] font-medium text-slate-600">0.002s</span>
                 </div>
               </motion.div>
             ))}
           </div>
        </div>
      </div>
    </div>
  );
}
