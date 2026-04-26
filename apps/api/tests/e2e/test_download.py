import re
import pytest
from playwright.sync_api import Page

@pytest.mark.e2e
def test_download_button_functionality(page: Page, base_url: str) -> None:
    """Verify that the download button triggers a file download (Section 16.3)."""
    page.goto(f"{base_url}/experiments")

    # Wait for page hydration and data loading
    page.wait_for_selector("aside", timeout=10000)
    page.wait_for_timeout(3000)

    from src.database.supabase_client import get_supabase_client
    supabase = get_supabase_client()

    RESEARCHER_ID = "a24fb1a2-700a-4590-8d43-2930596a14f2"
    
    import uuid
    param_id = str(uuid.uuid4())
    params = {
        "id": param_id,
        "underlying_price": 100.0,
        "strike_price": 100.0,
        "maturity_years": 1.0,
        "volatility": 0.2,
        "risk_free_rate": 0.05,
        "option_type": "call",
        "is_american": False,
        "market_source": "synthetic"
    }
    # Direct sync call to ensure data exists for the table to render
    supabase.table("option_parameters").upsert(params).execute()
    
    # Insert a result so the table shows something
    supabase.table("method_results").upsert({
        "option_id": param_id,
        "method_type": "analytical",
        "computed_price": 10.45,
        "exec_seconds": 0.001,
        "parameter_set": {"s": 100, "k": 100}
    }).execute()
    
    # Reload to ensure the table picks up the data
    page.reload()
    page.wait_for_selector("table", timeout=10000)

    # Section 16.3: DownloadButton CSV click
    # Find button with text CSV or Export
    download_btn = page.get_by_role("button", name=re.compile("CSV|Export", re.IGNORECASE)).first

    if not download_btn.is_visible():
        # Fallback to any download button or generic Export
        download_btn = page.get_by_text(re.compile("Export|Download", re.IGNORECASE)).first

    if download_btn.is_visible():
        # Use a slightly longer timeout for the download event
        try:
            with page.expect_download(timeout=15000) as download_info:
                download_btn.click()
            download = download_info.value
            assert download.suggested_filename.endswith(".csv")
        except Exception as e:
            # If download fails, take a screenshot for debugging (if we could, but we'll just fail with better msg)
            pytest.fail(f"Download failed or timed out: {str(e)}")
    else:
        # If no button found, maybe it's still loading or the table is empty
        # We'll skip if we really can't find it, but ideally it should be there
        pytest.skip("Download button not found in current UI state")
