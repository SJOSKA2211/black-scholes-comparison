"""All custom Prometheus metrics for the Black-Scholes research platform."""

from prometheus_client import Counter, Gauge, Histogram

# ── Pricing metrics ──────────────────────────────────────────────────────
PRICE_COMPUTATIONS_TOTAL = Counter(
    "black_scholes_price_computations_total",
    "Total option pricing computations by method and convergence status.",
    ["method_type", "option_type", "converged"],
)

PRICE_COMPUTATION_DURATION_SECONDS = Histogram(
    "black_scholes_price_computation_duration_seconds",
    "Duration of a single option pricing computation in seconds.",
    ["method_type"],
    buckets=[0.0001, 0.001, 0.01, 0.1, 0.5, 1.0, 5.0, 10.0],
)

PRICE_MAPE_GAUGE = Gauge(
    "black_scholes_price_mape_percent",
    "Latest MAPE vs analytical price for each method at ATM standard params.",
    ["method_type"],
)

# ── Experiment metrics ───────────────────────────────────────────────────
EXPERIMENTS_RUN_TOTAL = Counter(
    "black_scholes_experiments_run_total",
    "Total experiment grid computations completed.",
    ["method_type", "market_source"],
)

EXPERIMENT_GRID_PROGRESS = Gauge(
    "black_scholes_experiment_grid_progress_ratio",
    "Fraction of experiment grid completed (0.0 to 1.0).",
)

EXPERIMENT_ERRORS_TOTAL = Counter(
    "black_scholes_experiment_errors_total",
    "Non-finite pricing results logged to experiment_errors table.",
    ["method_type", "error_type"],
)

# ── Scraper metrics ───────────────────────────────────────────────────────
SCRAPE_RUNS_TOTAL = Counter(
    "black_scholes_scrape_runs_total",
    "Total scraper executions by market and final status.",
    ["market", "status"],
)

SCRAPE_ROWS_INSERTED = Gauge(
    "black_scholes_scrape_rows_inserted",
    "Number of market data rows inserted in the most recent scrape run.",
    ["market"],
)

SCRAPE_DURATION_SECONDS = Histogram(
    "black_scholes_scrape_duration_seconds",
    "Wall-clock duration of a complete scrape run.",
    ["market"],
    buckets=[5, 15, 30, 60, 120, 300, 600],
)

SCRAPE_ERRORS_TOTAL = Counter(
    "black_scholes_scrape_errors_total",
    "Non-fatal scraper errors per market and error type.",
    ["market", "error_type"],
)

# ── Supabase metrics ─────────────────────────────────────────────────────
SUPABASE_QUERY_DURATION_SECONDS = Histogram(
    "black_scholes_supabase_query_duration_seconds",
    "Duration of Supabase REST API calls.",
    ["table", "operation"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.5, 1.0, 2.0],
)

SUPABASE_ERRORS_TOTAL = Counter(
    "black_scholes_supabase_errors_total",
    "Failed Supabase API calls by table and operation.",
    ["table", "operation"],
)

# ── Notification metrics ─────────────────────────────────────────────────
NOTIFICATIONS_SENT_TOTAL = Counter(
    "black_scholes_notifications_sent_total",
    "Notifications dispatched by channel and severity.",
    ["channel", "severity"],
)
