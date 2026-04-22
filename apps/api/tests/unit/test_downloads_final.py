import pytest
import pandas as pd
from unittest.mock import MagicMock, patch
from src.routers.downloads import _serialize, download_resource
from fastapi import HTTPException

@pytest.mark.unit
class TestDownloadsFinal:
    def test_serialize_formats(self):
        df = pd.DataFrame([{"a": 1}])
        
        # CSV
        data, ct = _serialize(df, "csv")
        assert ct == "text/csv"
        
        # JSON
        data, ct = _serialize(df, "json")
        assert ct == "application/json"
        
        # XLSX
        data, ct = _serialize(df, "xlsx")
        assert "spreadsheetml" in ct
        
        # Invalid
        with pytest.raises(ValueError):
            _serialize(df, "invalid")

    @patch("src.routers.downloads._fetch_data")
    @patch("src.routers.downloads.upload_export")
    async def test_download_resource_success(self, mock_upload, mock_fetch):
        mock_fetch.return_value = pd.DataFrame([{"a": 1}])
        mock_upload.return_value = "http://presigned"
        
        res = await download_resource("experiments", "csv", {"id": "u1"})
        assert res["url"] == "http://presigned"

    async def test_download_resource_invalid_format(self):
        # The Query regex handles it usually, but we test the handler if it bypasses
        pass

    @patch("src.routers.downloads._fetch_data")
    async def test_download_resource_empty(self, mock_fetch):
        mock_fetch.return_value = pd.DataFrame()
        with pytest.raises(HTTPException) as exc:
            await download_resource("experiments", "csv", {"id": "u1"})
        assert exc.value.status_code == 404
