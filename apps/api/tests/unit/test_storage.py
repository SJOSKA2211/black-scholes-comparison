"""Unit tests for MinIO storage service."""
from __future__ import annotations
from unittest.mock import MagicMock, patch
import pytest
from src.storage.storage_service import upload_export, upload_scraper_artifact

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

@pytest.mark.unit
def test_upload_export_exception() -> None:
    """Verify export upload failure handling."""
    mock_minio = MagicMock()
    mock_minio.put_object.side_effect = Exception("Upload failed")
    
    with patch("src.storage.storage_service.get_minio", return_value=mock_minio):
        with pytest.raises(Exception) as exc:
            upload_export(b"data", "test.csv", "text/csv")
        assert str(exc.value) == "Upload failed"

@pytest.mark.unit
def test_upload_scraper_artifact() -> None:
    """Verify scraper artifact upload."""
    mock_minio = MagicMock()
    mock_minio.presigned_get_object.return_value = "http://minio/scraper_url"
    
    with patch("src.storage.storage_service.get_minio", return_value=mock_minio):
        url = upload_scraper_artifact(b"raw_html", "spy.html", "text/html")
        assert url == "http://minio/scraper_url"
        mock_minio.put_object.assert_called_once()
        _, kwargs = mock_minio.put_object.call_args
        assert kwargs["bucket_name"] == "bs-scraper"
