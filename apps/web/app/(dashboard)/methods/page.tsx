"use client";
import { Card, CardHeader, CardContent } from "@/components/ui/card";
import { useApi } from "@/hooks/useApi";
import { useQuery } from "@tanstack/react-query";
import { BookOpen, ShieldCheck, Zap, Layers, Target } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

export default function MethodsPage() {
  const { get } = useApi();
  const { data: methods, isLoading } = useQuery({
    queryKey: ["methods"],
    queryFn: () => get<any[]>("/api/v1/methods"),
  });

  return (
    <div className="space-y-10">
      <div>
        <h1 className="text-4xl font-black text-white tracking-tight">
          Numerical Methods
        </h1>
        <p className="text-slate-500 mt-2 text-lg">
          Documentation and performance benchmarks for the 12 core pricing
          algorithms.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-8">
        {isLoading
          ? [...Array(6)].map((_, i) => (
              <div
                key={i}
                className="h-64 rounded-3xl bg-slate-900/50 animate-pulse border border-slate-800"
              />
            ))
          : methods?.map((m, i) => (
              <Card
                key={m.id}
                delay={i * 0.05}
                className="group hover:border-blue-500/30 transition-all duration-500"
              >
                <CardHeader className="flex flex-row items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-center text-blue-500 group-hover:scale-110 transition-transform">
                      <Layers className="w-5 h-5" />
                    </div>
                    <h3 className="font-bold text-white text-base">{m.name}</h3>
                  </div>
                  {m.american_suitable && (
                    <Badge variant="success" className="text-[10px]">
                      American
                    </Badge>
                  )}
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="space-y-4">
                    <div className="flex justify-between items-center text-xs">
                      <span className="text-slate-500 font-bold uppercase tracking-widest flex items-center gap-2 text-[10px]">
                        <Target className="w-3 h-3" /> Convergence
                      </span>
                      <span className="text-blue-400 font-mono font-bold">
                        O({m.convergence_order})
                      </span>
                    </div>
                    <div className="flex justify-between items-center text-xs">
                      <span className="text-slate-500 font-bold uppercase tracking-widest flex items-center gap-2 text-[10px]">
                        <ShieldCheck className="w-3 h-3" /> Stability
                      </span>
                      <span
                        className={cn(
                          "font-bold",
                          m.stability_class === "Unconditional"
                            ? "text-emerald-500"
                            : "text-amber-500",
                        )}
                      >
                        {m.stability_class}
                      </span>
                    </div>
                    <div className="flex justify-between items-center text-xs">
                      <span className="text-slate-500 font-bold uppercase tracking-widest flex items-center gap-2 text-[10px]">
                        <Zap className="w-3 h-3" /> Efficiency
                      </span>
                      <span className="text-slate-300 font-bold">High</span>
                    </div>
                  </div>

                  <div className="pt-4 border-t border-slate-800/50">
                    <p className="text-xs text-slate-500 leading-relaxed italic">
                      {m.id === "analytical"
                        ? "The gold standard closed-form solution based on the 1973 Black-Scholes-Merton model."
                        : m.id.includes("fdm")
                          ? "Grid-based solution using finite difference approximations to the Black-Scholes PDE."
                          : m.id.includes("mc")
                            ? "Stochastic simulation of underlying price paths using risk-neutral valuation."
                            : "Discrete-time model approximating the continuous process through a tree structure."}
                    </p>
                  </div>
                </CardContent>
              </Card>
            ))}
      </div>

      <Card
        className="bg-gradient-to-br from-blue-600/10 to-transparent border-blue-500/20"
        delay={0.6}
      >
        <CardContent className="p-8 flex flex-col md:flex-row items-center gap-8">
          <div className="w-20 h-20 rounded-3xl bg-blue-600 flex items-center justify-center flex-shrink-0 shadow-2xl shadow-blue-500/50">
            <BookOpen className="w-10 h-10 text-white" />
          </div>
          <div>
            <h3 className="text-xl font-black text-white mb-2 text-[10px] uppercase tracking-[0.2em] opacity-50">
              Algorithm Selection Guide
            </h3>
            <h4 className="text-2xl font-black text-white mb-3">
              Optimal Pricing Strategy
            </h4>
            <p className="text-slate-400 text-sm max-w-2xl leading-relaxed">
              For European options,{" "}
              <span className="text-blue-400 font-bold underline">
                Analytical
              </span>{" "}
              is always preferred. For American options with complex boundaries,{" "}
              <span className="text-emerald-400 font-bold underline">
                Crank-Nicolson
              </span>{" "}
              or{" "}
              <span className="text-amber-400 font-bold underline">
                Binomial Richardson
              </span>
              provide the best balance of speed and O(N²) convergence.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
