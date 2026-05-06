"""Integration tests for storage compression and MinIO interactions."""
from __future__ import annotations
import gzip
import io
import requests
import pytest
from src.storage.storage_service import upload_export

@pytest.mark.integration
def test_storage_compression_roundtrip() -> None:
    """
    Verify that data uploaded with compression can be downloaded 
    and correctly decompressed. Uses real MinIO infrastructure.
    """
    test_data = b"Black-Scholes Research Platform - Compression Test Data " * 100
    filename = "test_compression.txt"
    content_type = "text/plain"
    
    # Upload with compression
    presigned_url = upload_export(
        data=test_data,
        filename=filename,
        content_type=content_type,
        compress=True
    )
    
    assert presigned_url is not None
    assert "https://" in presigned_url or "http://" in presigned_url
    
    # Download the data (MinIO is reachable via the presigned URL)
    # We use verify=False if it's self-signed in dev, but here it's likely internal
    response = requests.get(presigned_url, timeout=10)
    response.raise_for_status()
    
    downloaded_compressed_data = response.content
    
    # Decompress and verify
    with gzip.GzipFile(fileobj=io.BytesIO(downloaded_compressed_data)) as f:
        decompressed_data = f.read()
        
    assert decompressed_data == test_data
    assert len(downloaded_compressed_data) < len(test_data)  # Verify compression actually happened

@pytest.mark.integration
def test_storage_no_compression_roundtrip() -> None:
    """Verify that data uploaded without compression works correctly."""
    test_data = b"Raw data without compression"
    filename = "test_raw.txt"
    
    presigned_url = upload_export(
        data=test_data,
        filename=filename,
        content_type="text/plain",
        compress=False
    )
    
    response = requests.get(presigned_url, timeout=10)
    response.raise_for_status()
    
    assert response.content == test_data
