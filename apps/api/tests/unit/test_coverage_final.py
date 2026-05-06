"""Additional unit tests for full coverage."""
from __future__ import annotations
from datetime import date
from unittest.mock import MagicMock, patch
import pytest
from src.scrapers.base_scraper import BaseScraper
from src.storage.storage_service import upload_export

class DummyScraper(BaseScraper):
    async def _scrape(self, trade_date: date):
        return []

@pytest.mark.unit
@pytest.mark.asyncio
async def test_base_scraper_metrics() -> None:
    """Verify base scraper timing and status metrics."""
    scraper = DummyScraper("test")
    result = await scraper.run(date.today())
    assert result.execution_seconds > 0
    assert result.status == "success"

@pytest.mark.unit
def test_upload_export_error_handling() -> None:
    """Verify storage service handles MinIO errors."""
    mock_minio = MagicMock()
    mock_minio.put_object.side_effect = Exception("MinIO error")
    
    with patch("src.storage.storage_service.get_minio", return_value=mock_minio):
        with pytest.raises(Exception, match="MinIO error"):
            upload_export(b"data", "test.txt", "text/plain", compress=False)
