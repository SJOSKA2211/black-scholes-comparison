"""Unit tests for MinIO storage service."""
from __future__ import annotations
from unittest.mock import MagicMock, patch
import pytest
from src.storage.storage_service import upload_export

@pytest.mark.unit
def test_upload_export() -> None:
    """Verify export upload and URL generation."""
    mock_minio = MagicMock()
    mock_minio.presigned_get_object.return_value = "http://minio/url"
    
    with patch("src.storage.storage_service.get_minio", return_value=mock_minio):
        url = upload_export(b"data", "test.csv", "text/csv", compress=False)
        assert url == "http://minio/url"
        mock_minio.put_object.assert_called_once()
        _, kwargs = mock_minio.put_object.call_args
        assert kwargs["object_name"].endswith("test.csv")

@pytest.mark.unit
def test_upload_export_with_compression() -> None:
    """Verify export upload with compression."""
    mock_minio = MagicMock()
    mock_minio.presigned_get_object.return_value = "http://minio/url"
    
    with patch("src.storage.storage_service.get_minio", return_value=mock_minio):
        url = upload_export(b"data", "test.csv", "text/csv", compress=True)
        assert url == "http://minio/url"
        mock_minio.put_object.assert_called_once()
        
        # Check that the object_name was updated to include .gz
        _, kwargs = mock_minio.put_object.call_args
        assert kwargs["object_name"].endswith(".gz")
        assert kwargs["content_type"] == "application/gzip"
