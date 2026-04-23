import pytest
import requests

@pytest.mark.e2e
def test_prometheus_metrics_endpoint() -> None:
    """Verify that Prometheus metrics are correctly exposed (Section 16.3)."""
    # The metrics endpoint is usually on the API port
    metrics_url = "http://localhost:8000/metrics"
    
    try:
        response = requests.get(metrics_url, timeout=5)
        assert response.status_code == 200
        text = response.text
        
        # Check for core numerical metrics
        assert "black_scholes_price_computations_total" in text
        assert "black_scholes_price_computation_duration_seconds" in text
        
        # Check for infrastructure metrics
        assert "black_scholes_supabase_query_duration_seconds" in text
        assert "black_scholes_redis_cache_hits_total" in text
        assert "black_scholes_rabbitmq_tasks_published_total" in text
        assert "black_scholes_ws_connections_active" in text
        
        # Check for scraper/experiment metrics
        assert "black_scholes_scrape_runs_total" in text
        assert "black_scholes_experiments_run_total" in text
        
    except requests.exceptions.ConnectionError:
        pytest.skip("FastAPI server not reachable at http://localhost:8000")
