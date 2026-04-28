from prometheus_client import Counter, Gauge, Histogram

# Price Computations
PRICE_COMPUTATIONS_TOTAL = Counter(
    "black_scholes_price_computations_total",
    "Total pricing computations.",
    ["method_type", "option_type", "converged"],
)

PRICE_DURATION_SECONDS = Histogram(
    "black_scholes_price_computation_duration_seconds",
    "Pricing computation duration.",
    ["method_type"],
    buckets=[0.0001, 0.001, 0.01, 0.1, 0.5, 1.0, 5.0, 10.0],
)

PRICE_MAPE_GAUGE = Gauge(
    "black_scholes_price_mape_percent", "Latest MAPE vs analytical per method.", ["method_type"]
)

# Experiments
EXPERIMENTS_TOTAL = Counter(
    "black_scholes_experiments_run_total", "Grid experiments.", ["method_type", "market_source"]
)

EXPERIMENT_PROGRESS = Gauge(
    "black_scholes_experiment_grid_progress_ratio", "Fraction of grid completed (0-1)."
)

EXPERIMENT_ERRORS = Counter(
    "black_scholes_experiment_errors_total", "Non-finite results.", ["method_type", "error_type"]
)

# Scraper
SCRAPE_RUNS_TOTAL = Counter(
    "black_scholes_scrape_runs_total", "Scrape executions.", ["market", "status"]
)

SCRAPE_ROWS_INSERTED = Gauge(
    "black_scholes_scrape_rows_inserted", "Rows in latest scrape.", ["market"]
)

SCRAPE_DURATION = Histogram(
    "black_scholes_scrape_duration_seconds",
    "Scrape duration.",
    ["market"],
    buckets=[5, 15, 30, 60, 120, 300, 600],
)

SCRAPE_ERRORS_TOTAL = Counter(
    "black_scholes_scrape_errors_total", "Non-fatal scraper errors.", ["market", "error_type"]
)

# Infrastructure
SUPABASE_QUERY_DURATION = Histogram(
    "black_scholes_supabase_query_duration_seconds",
    "Supabase call duration.",
    ["table", "operation"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.5, 1.0, 2.0],
)

SUPABASE_ERRORS = Counter(
    "black_scholes_supabase_errors_total", "Failed Supabase calls.", ["table", "operation"]
)

REDIS_CACHE_HITS = Counter("black_scholes_redis_cache_hits_total", "Cache hits.", ["endpoint"])
REDIS_CACHE_MISSES = Counter(
    "black_scholes_redis_cache_misses_total", "Cache misses.", ["endpoint"]
)

RABBITMQ_TASKS_PUBLISHED = Counter(
    "black_scholes_rabbitmq_tasks_published_total", "Tasks queued.", ["queue"]
)
RABBITMQ_TASKS_CONSUMED = Counter(
    "black_scholes_rabbitmq_tasks_consumed_total", "Tasks processed.", ["queue", "status"]
)

WS_CONNECTIONS_ACTIVE = Gauge(
    "black_scholes_ws_connections_active", "Open WS connections.", ["channel"]
)

NOTIFICATIONS_SENT = Counter(
    "black_scholes_notifications_sent_total", "Notifications sent.", ["channel", "severity"]
)

MINIO_UPLOADS_TOTAL = Counter("black_scholes_minio_uploads_total", "MinIO uploads.", ["bucket"])
 
# Policy Enforcement
ZERO_MOCK_VIOLATIONS = Counter(
    "black_scholes_zero_mock_violations_total",
    "Total Zero-Mock policy violations detected at startup.",
    ["violation_type"]
)
