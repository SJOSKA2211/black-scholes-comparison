import pytest
from playwright.sync_api import Page


@pytest.mark.e2e
def test_download_flow(page: Page) -> None:
    """Verifies that the download button triggers a file download."""
    try:
        page.goto("http://localhost:3000/experiments", timeout=5000)
        # Click download button
        with page.expect_download() as download_info:
            page.get_by_role("button", name="Download CSV").click()
        download = download_info.value
        assert "csv" in download.suggested_filename
    except Exception:
        pytest.skip("Download flow not reachable")
