"use client";

import { motion } from "framer-motion";
import { Globe2, Play, AlertCircle, CheckCircle2, History, Database, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function ScrapersPage() {
  return (
    <div className="space-y-10">
      <header>
        <h1 className="text-4xl font-bold font-display tracking-tight text-white mb-2 flex items-center gap-3">
          <Globe2 className="w-8 h-8 text-cyan-400" />
          Market Data Scrapers
        </h1>
        <p className="text-slate-400 max-w-xl">
          Automated ingestion of equity and index options from global exchanges (CBOE, NSE). 
          Data is validated and indexed for research benchmarks.
        </p>
      </header>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
        {/* Scraper Cards */}
        <div className="xl:col-span-2 space-y-6">
           {[
             { name: "SPY (Standard & Poor's 500)", source: "CBOE / Yahoo Finance", status: "Idle", lastRun: "Today, 06:00 AM", color: "from-blue-500/20", border: "border-blue-500/30", iconColor: "text-blue-400" },
             { name: "NIFTY (Nifty 50 Index)", source: "NSE India", status: "Partial Success", lastRun: "Yesterday, 04:30 PM", color: "from-orange-500/20", border: "border-orange-500/30", iconColor: "text-orange-400" },
           ].map((scraper, i) => (
             <motion.div
               key={scraper.name}
               initial={{ opacity: 0, y: 10 }}
               animate={{ opacity: 1, y: 0 }}
               transition={{ delay: i * 0.1 }}
               className={`glass-card p-8 rounded-3xl border ${scraper.border} bg-gradient-to-br ${scraper.color} to-transparent relative overflow-hidden group`}
             >
               <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 relative z-10">
                 <div className="flex items-center gap-5">
                    <div className={`w-14 h-14 bg-slate-950 rounded-2xl flex items-center justify-center border border-white/10 group-hover:scale-110 transition-transform duration-500`}>
                       <Globe2 className={`w-7 h-7 ${scraper.iconColor}`} />
                    </div>
                    <div>
                       <h3 className="text-xl font-bold text-white mb-1">{scraper.name}</h3>
                       <p className="text-sm text-slate-400 font-medium">{scraper.source}</p>
                    </div>
                 </div>

                 <div className="flex flex-wrap items-center gap-4">
                    <div className="px-4 py-2 rounded-xl bg-slate-950/50 border border-white/5">
                       <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-0.5">Status</p>
                       <div className="flex items-center gap-1.5">
                          <div className={`w-1.5 h-1.5 rounded-full ${scraper.status === 'Idle' ? 'bg-indigo-400' : 'bg-amber-400'} animate-pulse`} />
                          <span className="text-xs font-bold text-white">{scraper.status}</span>
                       </div>
                    </div>
                    <div className="px-4 py-2 rounded-xl bg-slate-950/50 border border-white/5">
                       <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-0.5">Last Run</p>
                       <span className="text-xs font-bold text-white">{scraper.lastRun}</span>
                    </div>
                    <Button className="h-12 px-6 rounded-xl bg-white hover:bg-slate-100 text-slate-950 font-bold flex items-center gap-2 transition-all active:scale-95">
                       <Play className="w-4 h-4 fill-current" /> Trigger Scrape
                    </Button>
                 </div>
               </div>

               {/* Decorative Gradient Line */}
               <div className="absolute bottom-0 left-0 h-1 bg-gradient-to-r from-transparent via-white/10 to-transparent w-full" />
             </motion.div>
           ))}
        </div>

        {/* History Column */}
        <div className="space-y-6">
           <div className="glass-card p-8 rounded-3xl">
              <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
                <History className="w-5 h-5 text-indigo-400" />
                Audit Logs
              </h3>
              <div className="space-y-6">
                {[
                  { step: "Data Extraction", status: "Success", time: "06:01 AM", rows: 1240 },
                  { step: "Model Validation", status: "Success", time: "06:02 AM", rows: 1240 },
                  { step: "Database Upsert", status: "Success", time: "06:03 AM", rows: 1240 },
                  { step: "Cache Invalidation", status: "Success", time: "06:03 AM", rows: 0 },
                ].map((log, i) => (
                  <div key={i} className="flex items-start gap-4 relative">
                    {i < 3 && <div className="absolute left-2.5 top-6 bottom-[-1.5rem] w-px bg-slate-800" />}
                    <div className="w-5 h-5 rounded-full bg-emerald-500/20 flex items-center justify-center relative z-10 mt-0.5">
                       <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                    </div>
                    <div className="flex-1">
                       <div className="flex items-center justify-between">
                          <p className="text-sm font-bold text-slate-200">{log.step}</p>
                          <span className="text-[10px] font-mono text-slate-500">{log.time}</span>
                       </div>
                       <p className="text-xs text-slate-500 mt-0.5">{log.rows > 0 ? `Processed ${log.rows} option contracts` : 'Pipeline step complete'}</p>
                    </div>
                  </div>
                ))}
              </div>
              <Button variant="ghost" className="w-full mt-8 text-xs font-bold text-indigo-400 hover:bg-indigo-400/10 flex items-center gap-2 group">
                 Open Full Logs <ArrowRight className="w-3 h-3 group-hover:translate-x-1 transition-transform" />
              </Button>
           </div>

           <div className="glass-card p-6 rounded-3xl bg-indigo-600/5 border border-indigo-500/10">
              <div className="flex items-center gap-3 mb-4">
                 <Database className="w-5 h-5 text-indigo-400" />
                 <h4 className="font-bold text-white">Storage Health</h4>
              </div>
              <div className="space-y-4">
                 <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-500 font-medium">MinIO Bucket usage</span>
                    <span className="text-slate-300 font-bold">12.4 GB / 100 GB</span>
                 </div>
                 <div className="h-1.5 bg-slate-900 rounded-full overflow-hidden">
                    <div className="h-full bg-indigo-500 w-1/8" />
                 </div>
              </div>
           </div>
        </div>
      </div>
    </div>
  );
}
