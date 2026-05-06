"""Unit tests for storage service."""

import pytest
from unittest.mock import MagicMock, patch
from src.storage.storage_service import upload_export

@pytest.mark.unit
def test_upload_export_basic() -> None:
    """Test upload_export with mocks (since Zero-Mock is for integration, unit can use mocks)."""
    with patch("src.storage.storage_service.get_minio") as mock_get_minio:
        mock_client = MagicMock()
        mock_get_minio.return_value = mock_client
        mock_client.presigned_get_object.return_value = "http://minio/test.gz"
        
        data = b"test data"
        url = upload_export(data, "test.csv", "text/csv", compress=True)
        
        assert "test.gz" in url
        mock_client.put_object.assert_called_once()
        # Check if content_type was changed to gzip
        args, kwargs = mock_client.put_object.call_args
        assert kwargs["content_type"] == "application/gzip"
