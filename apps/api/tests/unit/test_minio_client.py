"""Unit tests for the MinIO client."""
from unittest.mock import patch, MagicMock
import pytest
from src.storage.minio_client import get_minio

@pytest.mark.unit
def test_get_minio():
    """Test that get_minio creates and returns a MinIO client."""
    get_minio.cache_clear()
    
    with patch("src.storage.minio_client.Minio") as mock_minio_class:
        mock_client = MagicMock()
        mock_minio_class.return_value = mock_client
        mock_client.bucket_exists.return_value = False
        
        client = get_minio()
        
        assert client == mock_client
        assert mock_client.make_bucket.call_count == 2 # bs-exports and bs-scraper
        
@pytest.mark.unit
def test_get_minio_bucket_exists():
    """Test that get_minio doesn't recreate existing buckets."""
    get_minio.cache_clear()
    
    with patch("src.storage.minio_client.Minio") as mock_minio_class:
        mock_client = MagicMock()
        mock_minio_class.return_value = mock_client
        mock_client.bucket_exists.return_value = True
        
        client = get_minio()
        
        assert client == mock_client
        assert mock_client.make_bucket.call_count == 0

@pytest.mark.unit
def test_get_minio_exception():
    """Test get_minio handling exceptions during bucket check."""
    get_minio.cache_clear()
    
    with patch("src.storage.minio_client.Minio") as mock_minio_class:
        mock_client = MagicMock()
        mock_minio_class.return_value = mock_client
        mock_client.bucket_exists.side_effect = Exception("error")
        
        client = get_minio()
        
        assert client == mock_client
