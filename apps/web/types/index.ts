export type OptionType = "call" | "put";
export type MarketSource = "synthetic" | "spy" | "nse";

export interface OptionParams {
  underlying_price: float;
  strike_price: float;
  maturity_years: float;
  volatility: float;
  risk_free_rate: float;
  option_type: OptionType;
  is_american: boolean;
  market_source: MarketSource;
}

export interface PriceResult {
  method_type: string;
  computed_price: float;
  exec_seconds: float;
  converged: boolean;
  replications?: number;
  confidence_interval?: [float, float];
  parameter_set: Record<string, any>;
}

export interface PriceRequest {
  params: OptionParams;
  methods: string[];
  persist?: boolean;
}

export interface PriceResponse {
  results: PriceResult[];
  analytical_reference: float;
  exec_ms: float;
}

export interface Experiment {
  id: string;
  option_id: string;
  method_type: string;
  parameter_set: Record<string, any>;
  computed_price: float;
  exec_seconds: float;
  run_at: string;
  option_parameters: OptionParams;
}

export interface MarketData {
  id: string;
  option_id: string;
  trade_date: string;
  bid_price: float;
  ask_price: float;
  mid_price: float;
  volume: int;
  open_interest: int;
  implied_vol?: float;
  data_source: MarketSource;
  option_parameters?: OptionParams;
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

export interface PaginatedResponse<T> {
  items: T[];
  total: int;
  page: int;
  page_size: int;
  has_next: boolean;
  has_prev: boolean;
}

// Helper types for floats/ints
type float = number;
type int = number;
