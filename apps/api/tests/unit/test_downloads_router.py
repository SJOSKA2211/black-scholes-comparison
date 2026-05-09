"""Unit tests for the downloads router."""
from __future__ import annotations
from typing import Any
import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.auth.dependencies import get_current_user
from unittest.mock import patch, MagicMock

client = TestClient(app)

def mock_get_current_user() -> dict[str, Any]:
    return {"id": "test-user", "email": "test@example.com"}

@pytest.mark.unit
def test_download_resource_csv() -> None:
    """Verify CSV download generation and upload."""
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    with patch("src.routers.downloads.list_option_parameters") as mock_list:
        mock_list.return_value = [{"id": "1", "strike": 100}]
        with patch("src.routers.downloads.upload_export") as mock_upload:
            mock_upload.return_value = "http://minio/presigned-url"
            
            response = client.get("/api/v1/download/options?format=csv")
            
            assert response.status_code == 200
            data = response.json()
            assert data["url"] == "http://minio/presigned-url"
            assert data["filename"].startswith("options_")
            assert data["filename"].endswith(".csv")
            assert mock_upload.called

@pytest.mark.unit
def test_download_resource_json() -> None:
    """Verify JSON download generation."""
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    with patch("src.routers.downloads.list_method_results") as mock_list:
        mock_list.return_value = [{"id": "1", "price": 10.5}]
        with patch("src.routers.downloads.upload_export") as mock_upload:
            mock_upload.return_value = "http://minio/presigned-url"
            
            response = client.get("/api/v1/download/results?format=json")
            
            assert response.status_code == 200
            assert response.json()["filename"].endswith(".json")

@pytest.mark.unit
def test_download_resource_xlsx() -> None:
    """Verify Excel download generation."""
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    with patch("src.routers.downloads.list_market_data") as mock_list:
        mock_list.return_value = [{"id": "1", "bid": 1.0}]
        with patch("src.routers.downloads.upload_export") as mock_upload:
            mock_upload.return_value = "http://minio/presigned-url"
            
            response = client.get("/api/v1/download/market?format=xlsx")
            
            assert response.status_code == 200
            assert response.json()["filename"].endswith(".xlsx")

@pytest.mark.unit
def test_download_unknown_resource() -> None:
    """Verify error for unknown resource."""
    app.dependency_overrides[get_current_user] = mock_get_current_user
    response = client.get("/api/v1/download/invalid")
    assert response.status_code == 400
    assert "Unknown resource" in response.json()["detail"]

@pytest.mark.unit
def test_download_empty_data() -> None:
    """Verify download handling for empty data sets."""
    app.dependency_overrides[get_current_user] = mock_get_current_user
    with patch("src.routers.downloads.list_option_parameters") as mock_list:
        mock_list.return_value = []
        with patch("src.routers.downloads.upload_export") as mock_upload:
            mock_upload.return_value = "http://minio/presigned-url"
            response = client.get("/api/v1/download/options")
            assert response.status_code == 200
            assert "url" in response.json()

@pytest.mark.unit
def test_download_exception_handling() -> None:
    """Verify 500 error on unexpected exceptions."""
    app.dependency_overrides[get_current_user] = mock_get_current_user
    with patch("src.routers.downloads.list_option_parameters", side_effect=Exception("Database down")):
        response = client.get("/api/v1/download/options")
        assert response.status_code == 500
        assert "Failed to generate download" in response.json()["detail"]
