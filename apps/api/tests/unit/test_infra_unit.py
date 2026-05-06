"""Additional unit tests for full coverage."""
from __future__ import annotations
from unittest.mock import MagicMock, patch
import pytest
from src.storage.minio_client import get_minio

@pytest.mark.unit
def test_minio_client_init() -> None:
    """Verify MinIO client initialization and bucket creation."""
    with patch("src.storage.minio_client.Minio") as mock_minio:
        mock_instance = mock_minio.return_value
        mock_instance.bucket_exists.return_value = False
        
        # This will trigger bucket creation
        client = get_minio()
        assert client == mock_instance
        mock_instance.make_bucket.assert_called_with("exports")

@pytest.mark.unit
def test_websocket_channels() -> None:
    """Verify WebSocket channels definition."""
    from src.websocket.channels import CHANNELS
    assert isinstance(CHANNELS, list)
