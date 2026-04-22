import pytest
import io
from unittest.mock import MagicMock, patch
from src.storage.storage_service import upload_export

@pytest.mark.unit
class TestStorageService:
    @patch("src.storage.storage_service.get_minio")
    def test_upload_export_success(self, mock_get_minio):
        # Setup
        mock_client = MagicMock()
        mock_get_minio.return_value = mock_client
        mock_client.presigned_get_object.return_value = "http://minio/url"
        
        data = b"csv,data"
        filename = "test.csv"
        content_type = "text/csv"
        
        # Execute
        url = upload_export(data, filename, content_type)
        
        # Verify
        assert url == "http://minio/url"
        mock_client.put_object.assert_called_once()
        args, kwargs = mock_client.put_object.call_args
        assert kwargs["bucket_name"] == "bs-exports"
        assert kwargs["content_type"] == content_type
        assert isinstance(kwargs["data"], io.BytesIO)
        assert kwargs["length"] == len(data)

    @patch("src.storage.storage_service.get_minio")
    def test_upload_export_custom_bucket(self, mock_get_minio):
        mock_client = MagicMock()
        mock_get_minio.return_value = mock_client
        
        upload_export(b"data", "file.txt", "text/plain", bucket="custom")
        
        assert mock_client.put_object.call_args.kwargs["bucket_name"] == "custom"

    @patch("src.storage.storage_service.get_minio")
    def test_upload_export_path_format(self, mock_get_minio):
        mock_client = MagicMock()
        mock_get_minio.return_value = mock_client
        
        upload_export(b"data", "test.csv", "text/csv")
        
        object_name = mock_client.put_object.call_args.kwargs["object_name"]
        # exports/YYYY/MM/DD/filename
        assert object_name.startswith("exports/")
        assert object_name.endswith("/test.csv")
        assert len(object_name.split("/")) == 5

    @patch("src.storage.storage_service.get_minio")
    def test_upload_export_expiry(self, mock_get_minio):
        mock_client = MagicMock()
        mock_get_minio.return_value = mock_client
        
        upload_export(b"data", "test.csv", "text/csv")
        
        mock_client.presigned_get_object.assert_called_once()
        expiry = mock_client.presigned_get_object.call_args.kwargs["expires"]
        assert expiry.total_seconds() == 3600
