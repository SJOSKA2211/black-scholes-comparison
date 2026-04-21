-- 001_initial_schema.sql
-- Master schema for Black-Scholes Research Platform

-- 1. user_profiles
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    display_name TEXT,
    avatar_url TEXT,
    role TEXT DEFAULT 'researcher' CHECK (role IN ('researcher', 'admin')),
    notification_preferences JSONB DEFAULT '{"email": true, "push": true, "in_app": true, "min_severity": "info"}',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- 2. option_parameters
CREATE TABLE IF NOT EXISTS option_parameters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    underlying_price FLOAT8 CHECK (underlying_price > 0),
    strike_price FLOAT8 CHECK (strike_price > 0),
    maturity_years FLOAT8 CHECK (maturity_years > 0),
    volatility FLOAT8 CHECK (volatility > 0),
    risk_free_rate FLOAT8 CHECK (risk_free_rate >= 0),
    option_type TEXT CHECK (option_type IN ('call', 'put')),
    is_american BOOL DEFAULT FALSE,
    market_source TEXT CHECK (market_source IN ('synthetic', 'spy', 'nse')),
    created_at TIMESTAMPTZ DEFAULT now(),
    created_by UUID REFERENCES auth.users(id),
    UNIQUE (underlying_price, strike_price, maturity_years, volatility, risk_free_rate, option_type, market_source)
);

-- 3. method_results
CREATE TABLE IF NOT EXISTS method_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    option_id UUID REFERENCES option_parameters(id) ON DELETE CASCADE,
    method_type TEXT,
    parameter_set JSONB DEFAULT '{}',
    parameter_hash TEXT,
    computed_price FLOAT8,
    exec_seconds FLOAT8 CHECK (exec_seconds >= 0),
    converged BOOL DEFAULT TRUE,
    replications INT4 DEFAULT 1 CHECK (replications >= 1),
    run_at TIMESTAMPTZ DEFAULT now(),
    run_by UUID REFERENCES auth.users(id),
    UNIQUE (option_id, method_type, parameter_hash)
);

-- 4. market_data
CREATE TABLE IF NOT EXISTS market_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    option_id UUID REFERENCES option_parameters(id) ON DELETE CASCADE,
    trade_date DATE,
    bid_price FLOAT8 CHECK (bid_price >= 0),
    ask_price FLOAT8 CHECK (ask_price > 0),
    mid_price FLOAT8 GENERATED ALWAYS AS ((bid_price + ask_price) / 2) STORED,
    volume INT4 DEFAULT 0 CHECK (volume >= 0),
    open_interest INT4 DEFAULT 0 CHECK (open_interest >= 0),
    implied_vol FLOAT8,
    data_source TEXT CHECK (data_source IN ('spy', 'nse')),
    UNIQUE (option_id, trade_date)
);

-- 5. validation_metrics
CREATE TABLE IF NOT EXISTS validation_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    option_id UUID REFERENCES option_parameters(id) ON DELETE CASCADE,
    method_result_id UUID REFERENCES method_results(id) ON DELETE CASCADE,
    absolute_error FLOAT8 CHECK (absolute_error >= 0),
    relative_pct_error FLOAT8,
    mape FLOAT8,
    market_deviation FLOAT8,
    computed_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE (option_id, method_result_id)
);

-- 6. scrape_runs
CREATE TABLE IF NOT EXISTS scrape_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    market TEXT CHECK (market IN ('spy', 'nse')),
    scraper_class TEXT,
    started_at TIMESTAMPTZ DEFAULT now(),
    finished_at TIMESTAMPTZ,
    rows_scraped INT4 DEFAULT 0,
    rows_validated INT4 DEFAULT 0,
    rows_inserted INT4 DEFAULT 0,
    error_count INT4 DEFAULT 0,
    status TEXT DEFAULT 'running' CHECK (status IN ('running', 'success', 'partial', 'failed')),
    triggered_by UUID REFERENCES auth.users(id)
);

-- 7. audit_log
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_run_id UUID,
    step_name TEXT,
    status TEXT CHECK (status IN ('started', 'completed', 'failed')),
    rows_affected INT4 DEFAULT 0,
    message TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 8. notifications
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT,
    body TEXT,
    severity TEXT CHECK (severity IN ('info', 'warning', 'error', 'critical')),
    channel TEXT CHECK (channel IN ('in_app', 'email', 'push')),
    read BOOL DEFAULT FALSE,
    action_url TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes
CREATE INDEX IF NOT EXISTS ix_method_results_method_type ON method_results(method_type);
CREATE INDEX IF NOT EXISTS ix_method_results_option_id ON method_results(option_id);
CREATE INDEX IF NOT EXISTS ix_method_results_run_at ON method_results(run_at DESC);
CREATE INDEX IF NOT EXISTS ix_method_results_jsonb ON method_results USING GIN(parameter_set);
CREATE INDEX IF NOT EXISTS ix_market_data_date ON market_data(trade_date DESC);
CREATE INDEX IF NOT EXISTS ix_market_data_source ON market_data(data_source);
CREATE INDEX IF NOT EXISTS ix_notifications_user_unread ON notifications(user_id, read) WHERE read = false;
CREATE INDEX IF NOT EXISTS ix_scrape_runs_status ON scrape_runs(market, status, started_at DESC);

-- Enable Realtime
ALTER PUBLICATION supabase_realtime ADD TABLE
    user_profiles,
    option_parameters,
    method_results,
    market_data,
    validation_metrics,
    scrape_runs,
    audit_log,
    notifications;

-- RLS
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own profile" ON user_profiles
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update their own profile" ON user_profiles
    FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Users can view their own notifications" ON notifications
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can update their own notifications" ON notifications
    FOR UPDATE USING (auth.uid() = user_id);
