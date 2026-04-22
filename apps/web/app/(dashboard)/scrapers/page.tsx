"use client";
import { Card, CardHeader, CardContent } from "@/components/ui/card";
import { useApi } from "@/hooks/useApi";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Database, Play, CheckCircle2, XCircle, Clock, RefreshCcw } from "lucide-react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { formatDate, cn } from "@/lib/utils";

export default function ScrapersPage() {
  const { post, get } = useApi();
  const queryClient = useQueryClient();

  const { data: runs, isLoading } = useQuery({
    queryKey: ["scrape-runs"],
    queryFn: () => get<any[]>("/api/v1/scrapers/runs"),
    refetchInterval: 5000,
  });

  const triggerMutation = useMutation({
    mutationFn: (market: string) => post("/api/v1/scrapers/trigger", { market }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["scrape-runs"] }),
  });

  const markets = [
    { id: "spy", name: "SPY (S&P 500 ETF)", source: "Yahoo Finance", frequency: "Daily" },
    { id: "nse", name: "NIFTY (NSE India)", source: "NSE India", frequency: "Weekly" },
  ];

  const getDuration = (start: string, finish?: string) => {
    if (!finish) return "Running...";
    const s = new Date(start).getTime();
    const f = new Date(finish).getTime();
    return `${((f - s) / 1000).toFixed(2)}s`;
  };

  return (
    <div className="space-y-10">
      <div>
        <h1 className="text-4xl font-black text-white tracking-tight">Data Scrapers</h1>
        <p className="text-slate-500 mt-2 text-lg">Manage and monitor high-frequency market data ingestion pipelines.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {markets.map((m) => (
          <Card key={m.id} delay={0.1}>
            <CardContent className="p-8">
              <div className="flex justify-between items-start mb-6">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-2xl bg-slate-900 border border-slate-800 flex items-center justify-center text-blue-500">
                    <Database className="w-6 h-6" />
                  </div>
                  <div>
                    <h3 className="font-black text-white text-lg">{m.name}</h3>
                    <p className="text-xs font-bold text-slate-500 uppercase tracking-widest">{m.source}</p>
                  </div>
                </div>
                <Badge variant="slate">{m.frequency}</Badge>
              </div>
              <Button 
                className="w-full h-12 gap-3" 
                onClick={() => triggerMutation.mutate(m.id)}
                disabled={triggerMutation.isPending}
              >
                <Play className="w-4 h-4" />
                {triggerMutation.isPending ? "Starting..." : "Trigger Manual Scrape"}
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card delay={0.3}>
        <CardHeader className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-slate-500" />
            <h3 className="font-bold text-white">Recent Execution History</h3>
          </div>
          <Button variant="ghost" size="sm" onClick={() => queryClient.invalidateQueries({ queryKey: ["scrape-runs"] })}>
            <RefreshCcw className="w-3 h-3 mr-2" />
            Refresh
          </Button>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-left min-w-[800px]">
              <thead>
                <tr className="border-b border-slate-800 text-slate-500 text-[10px] uppercase tracking-widest font-black">
                  <th className="px-8 py-5">Market</th>
                  <th className="px-8 py-5">Status</th>
                  <th className="px-8 py-5">Rows Scraped</th>
                  <th className="px-8 py-5">Started At</th>
                  <th className="px-8 py-5">Duration</th>
                  <th className="px-8 py-5 text-right">Errors</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {isLoading ? (
                    [...Array(3)].map((_, i) => <tr key={i} className="h-16 animate-pulse bg-slate-900/10" />)
                ) : (runs || []).map((run: any) => (
                  <tr key={run.id} className="hover:bg-slate-900/30 transition-colors">
                    <td className="px-8 py-6 font-bold text-white uppercase">{run.market}</td>
                    <td className="px-8 py-6">
                      <div className="flex items-center gap-2">
                        {run.status === 'success' ? <CheckCircle2 className="w-4 h-4 text-emerald-500" /> : 
                         run.status === 'running' ? <RefreshCcw className="w-4 h-4 text-blue-500 animate-spin" /> :
                         <XCircle className="w-4 h-4 text-red-500" />}
                        <span className={cn("text-xs font-bold capitalize", 
                          run.status === 'success' ? "text-emerald-500" : 
                          run.status === 'running' ? "text-blue-500" : "text-red-500"
                        )}>{run.status}</span>
                      </div>
                    </td>
                    <td className="px-8 py-6 font-mono text-sm text-slate-400">{run.rows_inserted} / {run.rows_scraped}</td>
                    <td className="px-8 py-6 text-slate-500 text-sm">{formatDate(run.started_at)}</td>
                    <td className="px-8 py-6 text-slate-500 text-sm font-mono">{getDuration(run.started_at, run.finished_at)}</td>
                    <td className="px-8 py-6 text-right font-mono text-xs">
                      <span className={run.error_count > 0 ? "text-red-500 font-bold" : "text-slate-600"}>
                          {run.error_count}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
