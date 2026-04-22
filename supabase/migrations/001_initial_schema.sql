-- 001_initial_schema.sql
-- Master schema for Black-Scholes Research Platform
-- Project: smawxojcohoqeqyksuvp

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

-- Robust migration: Ensure columns exist if table was created in an older version
ALTER TABLE method_results ADD COLUMN IF NOT EXISTS run_at TIMESTAMPTZ DEFAULT now();
ALTER TABLE method_results ADD COLUMN IF NOT EXISTS replications INT4 DEFAULT 1;

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

-- 9. scrape_errors
CREATE TABLE IF NOT EXISTS scrape_errors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scrape_run_id UUID REFERENCES scrape_runs(id) ON DELETE CASCADE,
    url TEXT,
    attempt INT4,
    error_type TEXT,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Performance Indexes
CREATE INDEX IF NOT EXISTS ix_method_results_method_type ON method_results(method_type);
CREATE INDEX IF NOT EXISTS ix_method_results_option_id ON method_results(option_id);
CREATE INDEX IF NOT EXISTS ix_method_results_run_at ON method_results(run_at DESC);
CREATE INDEX IF NOT EXISTS ix_method_results_jsonb ON method_results USING GIN(parameter_set);
CREATE INDEX IF NOT EXISTS ix_market_data_date ON market_data(trade_date DESC);
CREATE INDEX IF NOT EXISTS ix_market_data_source ON market_data(data_source);
CREATE INDEX IF NOT EXISTS ix_notifications_user_unread ON notifications(user_id, read) WHERE read = false;
CREATE INDEX IF NOT EXISTS ix_scrape_runs_status ON scrape_runs(market, status, started_at DESC);

-- RLS: enable on all tables
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE option_parameters ENABLE ROW LEVEL SECURITY;
ALTER TABLE method_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE market_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE validation_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE scrape_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE scrape_errors ENABLE ROW LEVEL SECURITY;

-- Anon key: SELECT on result tables
DROP POLICY IF EXISTS anon_read ON method_results;
CREATE POLICY anon_read ON method_results FOR SELECT TO anon USING (true);

DROP POLICY IF EXISTS anon_read ON market_data;
CREATE POLICY anon_read ON market_data    FOR SELECT TO anon USING (true);

DROP POLICY IF EXISTS anon_read ON option_parameters;
CREATE POLICY anon_read ON option_parameters FOR SELECT TO anon USING (true);

-- Service role: full access everywhere
DROP POLICY IF EXISTS svc_all ON user_profiles;
CREATE POLICY svc_all ON user_profiles FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS svc_all ON option_parameters;
CREATE POLICY svc_all ON option_parameters FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS svc_all ON method_results;
CREATE POLICY svc_all ON method_results FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS svc_all ON market_data;
CREATE POLICY svc_all ON market_data FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS svc_all ON validation_metrics;
CREATE POLICY svc_all ON validation_metrics FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS svc_all ON scrape_runs;
CREATE POLICY svc_all ON scrape_runs FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS svc_all ON audit_log;
CREATE POLICY svc_all ON audit_log FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS svc_all ON notifications;
CREATE POLICY svc_all ON notifications FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS svc_all ON scrape_errors;
CREATE POLICY svc_all ON scrape_errors FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Authenticated users: own notifications only
DROP POLICY IF EXISTS notif_owner ON notifications;
CREATE POLICY notif_owner ON notifications FOR ALL TO authenticated
    USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());

DROP POLICY IF EXISTS profile_owner ON user_profiles;
CREATE POLICY profile_owner ON user_profiles FOR ALL TO authenticated
    USING (id = auth.uid()) WITH CHECK (id = auth.uid());

-- 10. push_subscriptions
CREATE TABLE IF NOT EXISTS push_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    subscription_info JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE (user_id, subscription_info)
);

ALTER TABLE push_subscriptions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS push_owner ON push_subscriptions;
CREATE POLICY push_owner ON push_subscriptions FOR ALL TO authenticated
    USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());

DROP POLICY IF EXISTS push_svc ON push_subscriptions;
CREATE POLICY push_svc ON push_subscriptions FOR ALL TO service_role
    USING (true) WITH CHECK (true);

-- Profile trigger on auth.users INSERT
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.user_profiles (id, display_name, avatar_url)
    VALUES (new.id, new.raw_user_meta_data->>'full_name', new.raw_user_meta_data->>'avatar_url');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Enable Realtime for all tables (Idempotent SET TABLE)
ALTER PUBLICATION supabase_realtime SET TABLE
    user_profiles,
    option_parameters,
    method_results,
    market_data,
    validation_metrics,
    scrape_runs,
    audit_log,
    notifications,
    scrape_errors,
    push_subscriptions;
