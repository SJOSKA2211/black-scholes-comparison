"use client";
import { useState } from "react";
import { Card, CardContent } from "@/components/ui/Card";
import { useExperiments } from "@/hooks/useExperiments";
import { Badge } from "@/components/ui/Badge";
import { useDownload } from "@/hooks/useDownload";
import { Button } from "@/components/ui/Button";
import { Download, Search, ChevronLeft, ChevronRight } from "lucide-react";
import { formatDate, formatCurrency } from "@/lib/utils";

export default function ExperimentsPage() {
  const [page, setPage] = useState(1);
  const { data, isLoading } = useExperiments({ page, pageSize: 12 });
  const { download, downloading } = useDownload("experiments");

  return (
    <div className="space-y-10">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-6">
        <div>
          <h1 className="text-4xl font-black text-white tracking-tight">Experiment Results</h1>
          <p className="text-slate-500 mt-2 text-lg">Detailed logs of numerical method computations and benchmarking.</p>
        </div>
        <div className="flex gap-4 w-full md:w-auto">
          <div className="relative flex-1 md:w-64">
             <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
             <input 
                placeholder="Search methods..."
                className="w-full h-11 pl-11 pr-4 bg-slate-900 border border-slate-800 rounded-xl text-sm focus:outline-none focus:border-blue-500 transition-all"
             />
          </div>
          <Button variant="secondary" onClick={() => download("csv")} disabled={downloading}>
            <Download className="w-4 h-4 mr-2" />
            {downloading ? "Exporting..." : "Export"}
          </Button>
        </div>
      </div>

      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse min-w-[800px]">
              <thead>
                <tr className="border-b border-slate-800 text-slate-500 text-[10px] uppercase tracking-widest font-black">
                  <th className="px-8 py-5">Method Type</th>
                  <th className="px-8 py-5">Computed Price</th>
                  <th className="px-8 py-5">Latency</th>
                  <th className="px-8 py-5 text-center">Stability</th>
                  <th className="px-8 py-5">Execution Date</th>
                  <th className="px-8 py-5">Params</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {isLoading ? (
                    [...Array(6)].map((_, i) => (
                        <tr key={i} className="animate-pulse">
                            <td colSpan={6} className="px-8 py-6 h-16 bg-slate-900/10" />
                        </tr>
                    ))
                ) : (data?.items || []).map((exp) => (
                  <tr key={exp.id} className="hover:bg-slate-900/30 transition-colors group">
                    <td className="px-8 py-6">
                      <div className="flex items-center gap-4">
                        <div className="w-10 h-10 rounded-2xl bg-slate-800/50 flex items-center justify-center font-black text-sm text-slate-500 group-hover:text-blue-500 group-hover:bg-blue-500/10 transition-all border border-slate-800 group-hover:border-blue-500/20">
                          {exp.method_type.substring(0, 2).toUpperCase()}
                        </div>
                        <span className="font-bold text-white capitalize">{exp.method_type.replace(/_/g, ' ')}</span>
                      </div>
                    </td>
                    <td className="px-8 py-6 font-mono font-bold text-white text-lg">{formatCurrency(exp.computed_price)}</td>
                    <td className="px-8 py-6">
                        <div className="flex items-center gap-2">
                            <div className="w-1.5 h-1.5 rounded-full bg-blue-500" />
                            <span className="text-slate-400 text-xs font-mono">{(exp.exec_seconds * 1000).toFixed(3)}ms</span>
                        </div>
                    </td>
                    <td className="px-8 py-6 text-center">
                        <Badge variant="success">Converged</Badge>
                    </td>
                    <td className="px-8 py-6 text-slate-500 text-sm font-medium">{formatDate(exp.run_at)}</td>
                    <td className="px-8 py-6">
                      <div className="flex gap-2">
                        <Badge variant="slate" className="text-[10px] font-mono tracking-tighter">S:{exp.option_parameters.underlying_price}</Badge>
                        <Badge variant="slate" className="text-[10px] font-mono tracking-tighter">K:{exp.option_parameters.strike_price}</Badge>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      <div className="flex items-center justify-between">
         <p className="text-sm text-slate-500 font-medium">
            Showing <span className="text-slate-300">{(page-1)*12 + 1}</span> to <span className="text-slate-300">{Math.min(page*12, data?.total || 0)}</span> of <span className="text-slate-300">{data?.total || 0}</span> results
         </p>
         <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={() => setPage(p => Math.max(1, p-1))} disabled={page === 1}>
                <ChevronLeft className="w-4 h-4" />
            </Button>
            <Button variant="outline" size="sm" onClick={() => setPage(p => p+1)} disabled={!data?.has_next}>
                <ChevronRight className="w-4 h-4" />
            </Button>
         </div>
      </div>
    </div>
  );
}
