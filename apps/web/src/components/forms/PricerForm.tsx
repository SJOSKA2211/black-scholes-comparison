"use client";

import React, { useState, useEffect } from "react";
import { Slider } from "@/components/ui/slider";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Calculator, RefreshCw } from "lucide-react";
import { usePricer } from "@/hooks/usePricer";
import { OptionParams, MethodType } from "@/types";

const METHODS: { id: MethodType; name: string }[] = [
  { id: "analytical", name: "Analytical" },
  { id: "standard_mc", name: "Monte Carlo" },
  { id: "binomial_crr", name: "Binomial Tree" },
  { id: "implicit_fdm", name: "Implicit FDM" },
];

/**
 * Interactive Pricer Form with sliders.
 * Real-time calculation on value change.
 */
export function PricerForm() {
  const { price, results, isPricing } = usePricer();
  const [params, setParams] = useState<OptionParams>({
    underlying_price: 100,
    strike_price: 100,
    maturity_years: 1,
    volatility: 0.2,
    risk_free_rate: 0.05,
    option_type: "call",
    is_american: false,
    market_source: "synthetic",
  });

  const [selectedMethods, setSelectedMethods] = useState<MethodType[]>([
    "analytical",
    "standard_mc",
  ]);

  // Debounced auto-price
  useEffect(() => {
    const timer = setTimeout(() => {
      price(params, selectedMethods);
    }, 300);
    return () => clearTimeout(timer);
  }, [params, selectedMethods, price]);

  const handleSliderChange = (key: keyof OptionParams, val: number[]) => {
    setParams((prev) => ({ ...prev, [key]: val[0] }));
  };

  return (
    <Card className="shadow-lg border-2 border-primary/5">
      <CardHeader className="pb-3 border-b bg-muted/50">
        <CardTitle className="flex items-center gap-2 text-lg font-bold">
          <Calculator className="h-5 w-5 text-primary" />
          Live Option Pricer
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-6 space-y-8">
        {/* Parameters Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div className="space-y-6">
            <div className="space-y-3">
              <div className="flex justify-between items-baseline">
                <Label>Underlying Price (S)</Label>
                <span className="text-sm font-mono text-primary">${params.underlying_price.toFixed(2)}</span>
              </div>
              <Slider
                value={[params.underlying_price]}
                min={10}
                max={500}
                step={1}
                onValueChange={(v) => handleSliderChange("underlying_price", v)}
              />
            </div>

            <div className="space-y-3">
              <div className="flex justify-between items-baseline">
                <Label>Strike Price (K)</Label>
                <span className="text-sm font-mono text-primary">${params.strike_price.toFixed(2)}</span>
              </div>
              <Slider
                value={[params.strike_price]}
                min={10}
                max={500}
                step={1}
                onValueChange={(v) => handleSliderChange("strike_price", v)}
              />
            </div>
          </div>

          <div className="space-y-6">
            <div className="space-y-3">
              <div className="flex justify-between items-baseline">
                <Label>Volatility (σ)</Label>
                <span className="text-sm font-mono text-primary">{(params.volatility * 100).toFixed(1)}%</span>
              </div>
              <Slider
                value={[params.volatility]}
                min={0.01}
                max={1.0}
                step={0.01}
                onValueChange={(v) => handleSliderChange("volatility", v)}
              />
            </div>

            <div className="space-y-3">
              <div className="flex justify-between items-baseline">
                <Label>Time to Maturity (T)</Label>
                <span className="text-sm font-mono text-primary">{params.maturity_years.toFixed(2)}Y</span>
              </div>
              <Slider
                value={[params.maturity_years]}
                min={0.1}
                max={5}
                step={0.1}
                onValueChange={(v) => handleSliderChange("maturity_years", v)}
              />
            </div>
          </div>
        </div>

        {/* Method Selection */}
        <div className="pt-4 border-t">
          <Label className="mb-4 block text-sm font-semibold uppercase tracking-wider text-muted-foreground">
            Computation Methods
          </Label>
          <div className="flex flex-wrap gap-3">
            {METHODS.map((m) => (
              <Button
                key={m.id}
                variant={selectedMethods.includes(m.id) ? "default" : "outline"}
                size="sm"
                onClick={() =>
                  setSelectedMethods((prev) =>
                    prev.includes(m.id)
                      ? prev.filter((p) => p !== m.id)
                      : [...prev, m.id]
                  )
                }
                className="transition-all duration-300"
              >
                {m.name}
              </Button>
            ))}
          </div>
        </div>

        {/* Call/Put Switch */}
        <div className="flex items-center justify-between pt-4">
          <div className="flex items-center gap-2">
            <span className={`text-sm font-bold ${params.option_type === "call" ? "text-primary" : "text-muted-foreground"}`}>CALL</span>
            <Switch
              checked={params.option_type === "put"}
              onCheckedChange={(checked) =>
                setParams((prev) => ({ ...prev, option_type: checked ? "put" : "call" }))
              }
            />
            <span className={`text-sm font-bold ${params.option_type === "put" ? "text-primary" : "text-muted-foreground"}`}>PUT</span>
          </div>
          
          <Button 
            disabled={isPricing}
            onClick={() => price(params, selectedMethods)}
            className="gap-2"
          >
            <RefreshCw className={`h-4 w-4 ${isPricing ? "animate-spin" : ""}`} />
            Recalculate
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
