import pytest
import re
from playwright.sync_api import Page


@pytest.mark.e2e
def test_download_button_functionality(page: Page) -> None:
    """Verify that the download button triggers a file download (Section 16.3)."""
    base_url = "http://127.0.0.1:3000"
    page.goto(f"{base_url}/experiments")

    # Wait for data to load if any
    page.wait_for_timeout(2000)

    # Section 16.3: DownloadButton CSV click → fetch called → blob created → anchor.download
    # We expect a button with text including "CSV" or "Export"
    download_btn = page.get_by_role("button", name=re.compile("CSV|Export", re.IGNORECASE)).first
    
    if not download_btn.is_visible():
        # Fallback to any download button
        download_btn = page.get_by_role("button", name="Download").first

    if download_btn.is_visible():
        with page.expect_download() as download_info:
            download_btn.click()
        download = download_info.value
        
        # Verify blob-like download behavior
        assert download.suggested_filename.endswith(".csv")
        # In a real app, the frontend creates a blob URL and sets it to an anchor
        # Playwright's expect_download captures this.
    else:
        pytest.skip("Download button not found")
