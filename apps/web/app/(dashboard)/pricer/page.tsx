"use client";
import { useState, useEffect } from "react";
import { Card, CardHeader, CardContent } from "@/components/ui/card";
import { usePricer } from "@/hooks/usePricer";
import { Badge } from "@/components/ui/badge";
import { OptionParams, PriceResult } from "@/types";
import { Calculator, Zap } from "lucide-react";
import { motion } from "framer-motion";
import { formatCurrency, cn } from "@/lib/utils";
import { PricerForm } from "@/components/forms/PricerForm";
import { PriceBarChart } from "@/components/charts/PriceBarChart";

const ALL_METHODS = [
  "analytical",
  "explicit_fdm",
  "implicit_fdm",
  "crank_nicolson",
  "standard_mc",
  "antithetic_mc",
  "control_variate_mc",
  "quasi_mc",
  "binomial_crr",
  "trinomial",
  "binomial_crr_richardson",
  "trinomial_richardson",
];

export default function PricerPage() {
  const [params, setParams] = useState<OptionParams>({
    underlying_price: 100,
    strike_price: 100,
    maturity_years: 1.0,
    volatility: 0.2,
    risk_free_rate: 0.05,
    option_type: "call",
    is_american: false,
    market_source: "synthetic",
  });

  const { mutate, data, isPending, error } = usePricer();

  // Auto-price on slider change
  useEffect(() => {
    const timer = setTimeout(() => {
      console.log("Auto-triggering price update...", params);
      mutate({
        params,
        methods: ALL_METHODS,
      });
    }, 1000); // Increased for stability
    return () => clearTimeout(timer);
  }, [params, mutate]);

  return (
    <div className="space-y-10">
      <div>
        <h1 className="text-4xl font-black text-white tracking-tight">
          Live Option Pricer
        </h1>
        <p className="text-slate-500 mt-2 text-lg">
          Real-time cross-method computation for European and American options.
        </p>
      </div>

      {error && (
        <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-2xl text-red-500 text-sm font-bold">
          API Error: {error instanceof Error ? error.message : String(error)}
        </div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
        <PricerForm params={params} setParams={setParams} />

        <Card className="xl:col-span-2" delay={0.2}>
          <CardHeader className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Zap className="w-4 h-4 text-amber-500" />
              <h3 className="font-bold text-white">Cross-Method Results</h3>
            </div>
            <div className="flex items-center gap-3">
              {isPending && <Badge variant="warning">Computing...</Badge>}
              <button 
                onClick={() => mutate({ params, methods: ALL_METHODS, persist: true })}
                className="text-[10px] bg-blue-600 hover:bg-blue-500 px-3 py-1 rounded text-white font-bold uppercase transition-all"
                disabled={isPending}
              >
                Save to Lab
              </button>
              <button 
                onClick={() => mutate({ params, methods: ALL_METHODS })}
                className="text-[10px] bg-slate-800 hover:bg-slate-700 px-2 py-1 rounded text-slate-400 font-bold uppercase"
              >
                Refresh
              </button>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            {data && (
              <div className="bg-slate-900/50 p-4 rounded-2xl border border-slate-800/50">
                <PriceBarChart
                  data={data.results.map((r) => ({
                    method: r.method_type.replace(/_/g, " "),
                    price: r.computed_price,
                  }))}
                  analyticalPrice={data.analytical_reference}
                />
              </div>
            )}
            <div className="space-y-3">
              {data?.results.map((res: PriceResult, i: number) => (
                <motion.div
                  key={res.method_type}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.03 }}
                  className="flex items-center justify-between p-3 rounded-xl bg-slate-900/30 border border-slate-800 hover:border-slate-700 transition-all group"
                >
                  <div className="flex items-center gap-4">
                    <div className="w-9 h-9 rounded-lg bg-slate-800 flex items-center justify-center font-bold text-slate-500 group-hover:text-blue-400 group-hover:bg-blue-500/10 transition-all text-xs">
                      {res.method_type.substring(0, 2).toUpperCase()}
                    </div>
                    <div>
                      <p className="text-sm font-bold text-white capitalize">
                        {res.method_type.replace(/_/g, " ")}
                      </p>
                      <p className="text-[10px] font-mono text-slate-500 uppercase tracking-widest">
                        {res.exec_seconds.toFixed(4)}s
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-lg font-black text-white">
                      {formatCurrency(res.computed_price)}
                    </p>
                    {data.analytical_reference > 0 && (
                      <p
                        className={cn(
                          "text-[9px] font-bold uppercase tracking-tighter",
                          Math.abs(
                            res.computed_price - data.analytical_reference,
                          ) < 0.01
                            ? "text-emerald-500"
                            : "text-amber-500",
                        )}
                      >
                        Δ{" "}
                        {(
                          (Math.abs(
                            res.computed_price - data.analytical_reference,
                          ) /
                            data.analytical_reference) *
                          100
                        ).toFixed(4)}
                        %
                      </p>
                    )}
                  </div>
                </motion.div>
              ))}

              {!data && !isPending && (
                <div className="h-96 flex flex-col items-center justify-center text-slate-700">
                  <Calculator className="w-16 h-16 mb-4 opacity-5" />
                  <p className="text-sm font-bold">
                    Adjust sliders to begin computation
                  </p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
