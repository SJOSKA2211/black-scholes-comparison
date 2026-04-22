import pytest
from unittest.mock import MagicMock, patch
from src.storage.minio_client import get_minio
from src.storage.storage_service import upload_export
from minio.error import S3Error
import io

@pytest.mark.unit
class TestStorage:
    @patch("src.storage.minio_client.Minio")
    @patch("src.storage.minio_client.get_settings")
    def test_get_minio_init(self, mock_settings, mock_minio_class):
        get_minio.cache_clear()
        mock_settings.return_value.minio_endpoint = "localhost:9000"
        mock_settings.return_value.minio_access_key = "minio"
        mock_settings.return_value.minio_secret_key = "minio123"
        mock_client = mock_minio_class.return_value
        mock_client.bucket_exists.side_effect = [False, True]
        client = get_minio()
        assert client == mock_client
        mock_client.make_bucket.assert_called_once_with("bs-exports")
        
    @patch("src.storage.minio_client.Minio")
    @patch("src.storage.minio_client.get_settings")
    def test_get_minio_s3_error(self, mock_settings, mock_minio_class):
        get_minio.cache_clear()
        mock_client = mock_minio_class.return_value
        # Fix S3Error args: code, message, resource, request_id, host_id, response
        err = S3Error("code", "msg", "res", "req", "host", MagicMock())
        mock_client.bucket_exists.side_effect = err
        client = get_minio()
        assert client == mock_client

    @patch("src.storage.storage_service.get_minio")
    def test_upload_export(self, mock_get_minio):
        mock_client = mock_get_minio.return_value
        mock_client.presigned_get_object.return_value = "http://presigned-url"
        url = upload_export(b"data", "test.txt", "text/plain")
        assert url == "http://presigned-url"
        mock_client.put_object.assert_called_once()
