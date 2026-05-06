"""Expanded unit tests for StorageService."""
from __future__ import annotations
from unittest.mock import MagicMock, patch
import pytest
from src.storage.storage_service import upload_export

@pytest.mark.unit
def test_upload_export_logic() -> None:
    """Verify that upload_export calls minio and returns a URL."""
    mock_minio = MagicMock()
    mock_minio.presigned_get_object.return_value = "https://minio.test/exports/123"
    
    with patch("src.storage.storage_service.get_minio", return_value=mock_minio):
        data = b"test data content"
        url = upload_export(data, filename="test.json", content_type="application/json", compress=False)
        
        assert url == "https://minio.test/exports/123"
        # Verify minio.put_object was called
        args, kwargs = mock_minio.put_object.call_args
        assert kwargs["bucket_name"] == "bs-exports"
        assert "test.json" in kwargs["object_name"]

@pytest.mark.unit
def test_upload_export_with_compression_logic() -> None:
    """Verify compression logic changes filename and content type."""
    mock_minio = MagicMock()
    mock_minio.presigned_get_object.return_value = "https://minio.test/exports/123.gz"
    
    with patch("src.storage.storage_service.get_minio", return_value=mock_minio):
        data = b"test data content"
        upload_export(data, filename="test.json", content_type="application/json", compress=True)
        
        _, kwargs = mock_minio.put_object.call_args
        assert kwargs["object_name"].endswith(".json.gz")
        assert kwargs["content_type"] == "application/gzip"
