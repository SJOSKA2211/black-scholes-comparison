export type MethodType =
  | "analytical"
  | "explicit_fdm"
  | "implicit_fdm"
  | "crank_nicolson"
  | "standard_mc"
  | "antithetic_mc"
  | "control_variate_mc"
  | "quasi_mc"
  | "binomial_crr"
  | "trinomial"
  | "binomial_crr_richardson"
  | "trinomial_richardson";

export type OptionType = "call" | "put";
export type MarketSource = "synthetic" | "spy" | "nse";

export interface OptionParams {
  underlying_price: number;
  strike_price: number;
  maturity_years: number;
  volatility: number;
  risk_free_rate: number;
  option_type: OptionType;
  is_american: boolean;
  market_source: MarketSource;
}

export interface PriceResult {
  method_type: MethodType;
  computed_price: number;
  exec_seconds: number;
  converged: boolean;
  replications: number;
  parameter_set: Record<string, any>;
  confidence_interval?: [number, number];
}

export interface PriceRequest {
  params: OptionParams;
  methods: MethodType[];
}

export interface PriceResponse {
  results: PriceResult[];
  analytical_reference: number;
  exec_ms: number;
}

export interface Notification {
  id: string;
  user_id: string;
  title: string;
  body: string;
  severity: "info" | "warning" | "error" | "critical";
  channel: "in_app" | "email" | "push";
  read: boolean;
  action_url?: string;
  created_at: string;
}

export type DownloadFormat = "csv" | "json" | "xlsx";
export type DownloadResource = "experiments" | "market-data" | "validation";
