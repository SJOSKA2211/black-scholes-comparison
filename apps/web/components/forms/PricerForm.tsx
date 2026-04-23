"use client";
import { OptionParams, OptionType, MarketSource } from "@/types";
import { Card, CardHeader, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import {
  Calculator,
  Globe,
  TrendingUp,
  Clock,
  Percent,
  ShieldCheck,
} from "lucide-react";

interface PricerFormProps {
  params: OptionParams;
  setParams: (params: OptionParams) => void;
}

export function PricerForm({ params, setParams }: PricerFormProps) {
  const updateParam = (key: keyof OptionParams, value: any) => {
    setParams({ ...params, [key]: value });
  };

  return (
    <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-xl">
      <CardHeader>
        <div className="flex items-center gap-2">
          <Calculator className="w-4 h-4 text-blue-500" />
          <h3 className="font-bold text-white uppercase tracking-wider text-sm">
            Parameters
          </h3>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label className="text-xs text-slate-500 flex items-center gap-2">
                <Globe className="w-3 h-3" /> Underlying Price
              </Label>
              <Input
                type="number"
                value={params.underlying_price}
                onChange={(e) =>
                  updateParam("underlying_price", parseFloat(e.target.value))
                }
                className="bg-slate-950 border-slate-800 text-white font-bold"
              />
            </div>
            <div className="space-y-2">
              <Label className="text-xs text-slate-500 flex items-center gap-2">
                <ShieldCheck className="w-3 h-3" /> Strike Price
              </Label>
              <Input
                type="number"
                value={params.strike_price}
                onChange={(e) =>
                  updateParam("strike_price", parseFloat(e.target.value))
                }
                className="bg-slate-950 border-slate-800 text-white font-bold"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label className="text-xs text-slate-500 flex items-center gap-2">
                <Clock className="w-3 h-3" /> Maturity (Years)
              </Label>
              <Input
                type="number"
                step="0.01"
                value={params.maturity_years}
                onChange={(e) =>
                  updateParam("maturity_years", parseFloat(e.target.value))
                }
                className="bg-slate-950 border-slate-800 text-white font-bold"
              />
            </div>
            <div className="space-y-2">
              <Label className="text-xs text-slate-500 flex items-center gap-2">
                <TrendingUp className="w-3 h-3" /> Volatility (σ)
              </Label>
              <Input
                type="number"
                step="0.01"
                value={params.volatility}
                onChange={(e) =>
                  updateParam("volatility", parseFloat(e.target.value))
                }
                className="bg-slate-950 border-slate-800 text-white font-bold"
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label className="text-xs text-slate-500 flex items-center gap-2">
              <Percent className="w-3 h-3" /> Risk-Free Rate
            </Label>
            <Input
              type="number"
              step="0.001"
              value={params.risk_free_rate}
              onChange={(e) =>
                updateParam("risk_free_rate", parseFloat(e.target.value))
              }
              className="bg-slate-950 border-slate-800 text-white font-bold"
            />
          </div>
        </div>

        <div className="pt-4 border-t border-slate-800 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label className="text-xs text-slate-500 uppercase tracking-widest">
                Type
              </Label>
              <Select
                value={params.option_type}
                onValueChange={(v: string) =>
                  updateParam("option_type", v as OptionType)
                }
              >
                <SelectTrigger className="bg-slate-950 border-slate-800 text-white font-bold">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-slate-900 border-slate-800 text-white">
                  <SelectItem value="call">Call</SelectItem>
                  <SelectItem value="put">Put</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label className="text-xs text-slate-500 uppercase tracking-widest">
                Source
              </Label>
              <Select
                value={params.market_source}
                onValueChange={(v: string) =>
                  updateParam("market_source", v as MarketSource)
                }
              >
                <SelectTrigger className="bg-slate-950 border-slate-800 text-white font-bold">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-slate-900 border-slate-800 text-white">
                  <SelectItem value="synthetic">Synthetic</SelectItem>
                  <SelectItem value="spy">SPY (Live)</SelectItem>
                  <SelectItem value="nse">NSE (Live)</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="flex items-center justify-between p-3 rounded-lg bg-slate-950/50 border border-slate-800">
            <div className="space-y-0.5">
              <Label className="text-xs font-bold text-white">
                American Option
              </Label>
              <p className="text-[10px] text-slate-500">
                Enable early exercise modeling
              </p>
            </div>
            <Switch
              checked={params.is_american}
              onCheckedChange={(v) => updateParam("is_american", v)}
            />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
