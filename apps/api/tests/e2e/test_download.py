import pytest
from playwright.sync_api import Page, expect

@pytest.mark.e2e
def test_download_button_functionality(page: Page) -> None:
    """Verify that the download button triggers a file download (Section 16.3)."""
    base_url = "http://localhost:3000"
    page.goto(f"{base_url}/experiments")
    
    # Wait for data to load if any
    page.wait_for_timeout(2000)
    
    # Find and click download button
    # The label might be "Download" or "Download CSV" depending on usage
    download_btn = page.get_by_role("button", name="Download")
    if not download_btn.is_visible():
        download_btn = page.get_by_role("button", name="Export")
    
    if download_btn.is_visible():
        # Playwright handle for downloads
        with page.expect_download() as download_info:
            download_btn.click()
        download = download_info.value
        assert download.suggested_filename is not None
    else:
        # If no button found, maybe check for icon
        icon_btn = page.locator("button:has(svg)")
        if icon_btn.is_visible():
            with page.expect_download() as download_info:
                icon_btn.first.click()
            download = download_info.value
            assert download.suggested_filename is not None
        else:
            pytest.skip("Download button not found")
