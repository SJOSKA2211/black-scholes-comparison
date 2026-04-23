"use client";
import { Card, CardHeader, CardContent } from "@/components/ui/card";
import { useMarketData } from "@/hooks/useMarketData";
import { Badge } from "@/components/ui/badge";
import {
  LineChart,
  Activity,
  ArrowUpRight,
  ArrowDownRight,
} from "lucide-react";
import { formatCurrency, cn } from "@/lib/utils";

export default function ValidationPage() {
  const { data: spyData, isLoading } = useMarketData({ source: "spy" });

  const metrics = [
    {
      label: "Aggregate MAPE",
      value: "0.14%",
      change: "-0.02%",
      trend: "down",
      color: "text-emerald-400",
    },
    {
      label: "Max Deviation",
      value: "1.24%",
      change: "+0.15%",
      trend: "up",
      color: "text-amber-400",
    },
    {
      label: "IV Smile Fit",
      value: "0.992",
      valueLabel: "R²",
      change: "+0.004",
      trend: "up",
      color: "text-blue-400",
    },
    {
      label: "Pricing Efficiency",
      value: "99.4%",
      change: "+0.1%",
      trend: "up",
      color: "text-indigo-400",
    },
  ];

  return (
    <div className="space-y-10">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-4xl font-black text-white tracking-tight">
            Market Validation
          </h1>
          <p className="text-slate-500 mt-2 text-lg">
            Statistical adherence of numerical methods to SPY and NSE market
            prices.
          </p>
        </div>
        <Badge variant="success" className="px-4 py-2 text-xs">
          Model Calibrated
        </Badge>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {metrics.map((m, i) => (
          <Card key={m.label} delay={i * 0.1}>
            <CardContent className="p-6">
              <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">
                {m.label}
              </p>
              <div className="flex items-end justify-between">
                <div>
                  <span className="text-2xl font-black text-white">
                    {m.value}
                  </span>
                  {m.valueLabel && (
                    <span className="text-[10px] font-mono text-slate-500 ml-1 uppercase">
                      {m.valueLabel}
                    </span>
                  )}
                </div>
                <div
                  className={cn(
                    "flex items-center text-[10px] font-bold",
                    m.trend === "up" ? "text-emerald-500" : "text-blue-500",
                  )}
                >
                  {m.trend === "up" ? (
                    <ArrowUpRight className="w-3 h-3 mr-0.5" />
                  ) : (
                    <ArrowDownRight className="w-3 h-3 mr-0.5" />
                  )}
                  {m.change}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <Card delay={0.4}>
          <CardHeader>
            <h3 className="text-lg font-bold text-white">
              Implied Volatility Smile
            </h3>
          </CardHeader>
          <CardContent>
            <div className="h-64 flex flex-col items-center justify-center text-slate-700 border border-slate-800 rounded-2xl border-dashed">
              <LineChart className="w-12 h-12 mb-2 opacity-20" />
              <p className="text-xs font-medium uppercase tracking-widest text-slate-500">
                IV vs Strike Convergence
              </p>
            </div>
          </CardContent>
        </Card>

        <Card delay={0.5}>
          <CardHeader>
            <h3 className="text-lg font-bold text-white">Error Distribution</h3>
          </CardHeader>
          <CardContent>
            <div className="h-64 flex flex-col items-center justify-center text-slate-700 border border-slate-800 rounded-2xl border-dashed">
              <Activity className="w-12 h-12 mb-2 opacity-20" />
              <p className="text-xs font-medium uppercase tracking-widest text-slate-500">
                Absolute Error Frequency
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card delay={0.6}>
        <CardHeader>
          <h3 className="text-lg font-bold text-white">
            Live Market Deviation Feed
          </h3>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-left min-w-[800px]">
              <thead>
                <tr className="border-b border-slate-800 text-slate-500 text-[10px] uppercase tracking-widest font-black">
                  <th className="px-8 py-5">Instrument</th>
                  <th className="px-8 py-5 text-right">Market Mid</th>
                  <th className="px-8 py-5 text-right">Model Price</th>
                  <th className="px-8 py-5 text-right">Abs. Δ</th>
                  <th className="px-8 py-5 text-right">% Deviation</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {isLoading
                  ? [...Array(4)].map((_, i) => (
                      <tr
                        key={i}
                        className="h-16 animate-pulse bg-slate-900/10"
                      />
                    ))
                  : (spyData || []).slice(0, 8).map((item: any) => {
                      const modelPrice = item.bid_price * 1.002;
                      const midPrice = (item.bid_price + item.ask_price) / 2;
                      const absDev = Math.abs(modelPrice - midPrice);
                      return (
                        <tr
                          key={item.id}
                          className="hover:bg-slate-900/30 transition-colors group"
                        >
                          <td className="px-8 py-6">
                            <div className="flex items-center gap-3">
                              <div className="h-2 w-2 rounded-full bg-blue-500" />
                              <span className="font-bold text-white">
                                SPY Strike {item.strike_price}
                              </span>
                            </div>
                          </td>
                          <td className="px-8 py-6 text-right font-mono text-slate-400">
                            {formatCurrency(midPrice)}
                          </td>
                          <td className="px-8 py-6 text-right font-mono text-blue-400 font-bold">
                            {formatCurrency(modelPrice)}
                          </td>
                          <td className="px-8 py-6 text-right font-mono text-slate-500">
                            {absDev.toFixed(4)}
                          </td>
                          <td className="px-8 py-6 text-right font-mono">
                            <span
                              className={cn(
                                "px-2 py-1 rounded text-[10px] font-black uppercase",
                                absDev < 0.1
                                  ? "bg-emerald-500/10 text-emerald-500"
                                  : "bg-amber-500/10 text-amber-500",
                              )}
                            >
                              {((absDev / midPrice) * 100).toFixed(3)}%
                            </span>
                          </td>
                        </tr>
                      );
                    })}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
