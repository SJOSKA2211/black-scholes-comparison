"use client";
import { useState, useEffect } from "react";
import { Card, CardHeader, CardContent } from "@/components/ui/card";
import { usePricer } from "@/hooks/usePricer";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { OptionParams, PriceResult } from "@/types";
import { Sliders, Calculator, Zap } from "lucide-react";
import { motion } from "framer-motion";
import { formatCurrency, cn } from "@/lib/utils";

const ALL_METHODS = [
    "analytical", "explicit_fdm", "implicit_fdm", "crank_nicolson", 
    "standard_mc", "antithetic_mc", "control_variate_mc", "quasi_mc", 
    "binomial_crr", "trinomial", "binomial_crr_richardson", "trinomial_richardson"
];

interface SliderProps {
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  onChange: (v: number) => void;
  unit?: string;
}

const Slider = ({ label, value, min, max, step, onChange, unit = "" }: SliderProps) => (
  <div className="space-y-3">
    <div className="flex justify-between items-center">
      <label className="text-xs font-bold text-slate-500 uppercase tracking-widest">{label}</label>
      <span className="text-sm font-mono text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded-lg border border-blue-500/20">
          {value}{unit}
      </span>
    </div>
    <input
      type="range"
      min={min}
      max={max}
      step={step}
      value={value}
      onChange={(e) => onChange(parseFloat(e.target.value))}
      className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-blue-500"
    />
  </div>
);

export default function PricerPage() {
  const [params, setParams] = useState<OptionParams>({
    underlying_price: 100,
    strike_price: 100,
    maturity_years: 1.0,
    volatility: 0.20,
    risk_free_rate: 0.05,
    option_type: "call",
    is_american: false,
    market_source: "synthetic"
  });

  const { mutate, data, isPending } = usePricer();

  // Auto-price on slider change
  useEffect(() => {
    const timer = setTimeout(() => {
        mutate({
            params,
            methods: ALL_METHODS
        });
    }, 400);
    return () => clearTimeout(timer);
  }, [params, mutate]);

  return (
    <div className="space-y-10">
      <div>
        <h1 className="text-4xl font-black text-white tracking-tight">Live Option Pricer</h1>
        <p className="text-slate-500 mt-2 text-lg">Real-time cross-method computation for European and American options.</p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
        <Card className="xl:col-span-1" delay={0.1}>
          <CardHeader className="flex items-center gap-2">
            <Sliders className="w-4 h-4 text-blue-500" />
            <h3 className="font-bold text-white">Parameters</h3>
          </CardHeader>
          <CardContent className="space-y-8">
            <Slider label="Underlying Price" value={params.underlying_price} min={10} max={1000} step={1} unit="$" onChange={(v) => setParams({...params, underlying_price: v})} />
            <Slider label="Strike Price" value={params.strike_price} min={10} max={1000} step={1} unit="$" onChange={(v) => setParams({...params, strike_price: v})} />
            <Slider label="Maturity (Years)" value={params.maturity_years} min={0.1} max={5} step={0.1} unit="y" onChange={(v) => setParams({...params, maturity_years: v})} />
            <Slider label="Volatility" value={params.volatility} min={0.01} max={1.5} step={0.01} unit="σ" onChange={(v) => setParams({...params, volatility: v})} />
            <Slider label="Risk-Free Rate" value={params.risk_free_rate} min={0.0} max={0.2} step={0.01} unit="%" onChange={(v) => setParams({...params, risk_free_rate: v})} />
            
            <div className="grid grid-cols-2 gap-4 pt-4">
               <Button 
                 variant={params.option_type === 'call' ? 'primary' : 'outline'}
                 onClick={() => setParams({...params, option_type: 'call'})}
               >Call</Button>
               <Button 
                 variant={params.option_type === 'put' ? 'primary' : 'outline'}
                 onClick={() => setParams({...params, option_type: 'put'})}
               >Put</Button>
            </div>
          </CardContent>
        </Card>

        <Card className="xl:col-span-2" delay={0.2}>
          <CardHeader className="flex items-center justify-between">
            <div className="flex items-center gap-2">
                <Zap className="w-4 h-4 text-amber-500" />
                <h3 className="font-bold text-white">Cross-Method Results</h3>
            </div>
            {isPending && <Badge variant="warning">Computing...</Badge>}
          </CardHeader>
          <CardContent>
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
                                <p className="text-sm font-bold text-white capitalize">{res.method_type.replace(/_/g, ' ')}</p>
                                <p className="text-[10px] font-mono text-slate-500 uppercase tracking-widest">{res.exec_seconds.toFixed(4)}s</p>
                            </div>
                        </div>
                        <div className="text-right">
                            <p className="text-lg font-black text-white">{formatCurrency(res.computed_price)}</p>
                            {data.analytical_reference > 0 && (
                                <p className={cn("text-[9px] font-bold uppercase tracking-tighter", 
                                    Math.abs(res.computed_price - data.analytical_reference) < 0.01 ? "text-emerald-500" : "text-amber-500")}>
                                    Δ {(Math.abs(res.computed_price - data.analytical_reference) / data.analytical_reference * 100).toFixed(4)}%
                                </p>
                            )}
                        </div>
                    </motion.div>
                ))}

                {!data && !isPending && (
                    <div className="h-96 flex flex-col items-center justify-center text-slate-700">
                        <Calculator className="w-16 h-16 mb-4 opacity-5" />
                        <p className="text-sm font-bold">Adjust sliders to begin computation</p>
                    </div>
                )}
             </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
