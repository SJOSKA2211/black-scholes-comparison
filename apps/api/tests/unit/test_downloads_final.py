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

    @patch("src.routers.downloads.get_experiments")
    @patch("src.routers.downloads.get_market_data")
    async def test_fetch_data_logic(self, mock_get_market, mock_get_exp):
        from src.routers.downloads import _fetch_data
        
        # Experiments
        mock_get_exp.return_value = {"items": [{"id": "e1"}]} # Note: actually extrait from "items" or "data"?
        # Wait, let's check downloads.py line 26: data = results_dict.get("data", [])
        # But get_experiments returns {"items": ..., "total": ...}
        # Let's fix downloads.py to use "items" if that's what it returns.
        
        mock_get_exp.return_value = {"items": [{"id": "e1"}]}
        df = await _fetch_data("experiments")
        assert not df.empty
        
        # Market
        mock_get_market.return_value = [{"id": "m1"}]
        df = await _fetch_data("market_data")
        assert not df.empty
        
        # Invalid
        with pytest.raises(ValueError):
            await _fetch_data("unknown")

    @patch("src.routers.downloads._fetch_data")
    async def test_download_resource_empty(self, mock_fetch):
        mock_fetch.return_value = pd.DataFrame()
        with pytest.raises(HTTPException) as exc:
            await download_resource("experiments", "csv", {"id": "u1"})
        assert exc.value.status_code == 404

    @patch("src.routers.downloads._fetch_data")
    async def test_download_resource_failure(self, mock_fetch):
        mock_fetch.side_effect = Exception("Generic fail")
        with pytest.raises(HTTPException) as exc:
            await download_resource("experiments", "csv", {"id": "u1"})
        assert exc.value.status_code == 500
