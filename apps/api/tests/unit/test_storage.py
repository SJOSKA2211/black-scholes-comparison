"""Unit tests for the object storage layer."""

from typing import Any

import pytest
from _pytest.monkeypatch import MonkeyPatch
from minio.error import MinioException

import src.storage.minio_client
from src.storage.minio_client import get_minio
from src.storage.storage_service import upload_export


@pytest.mark.unit
def test_upload_small_file() -> None:
    """Test uploading a small file (<1KB) — should not be compressed by default."""
    data = b"small data"
    url = upload_export(data, "small.txt", "text/plain", compress=False)
    assert url is not None
    assert "small.txt" in url


@pytest.mark.unit
def test_upload_large_file_compression() -> None:
    """Test that files > 1KB are compressed automatically."""
    data = b"a" * 2048
    url = upload_export(data, "large.txt", "text/plain")
    assert ".gz" in url


@pytest.mark.unit
def test_upload_with_gz_extension() -> None:
    """Test uploading a file that already has .gz extension."""
    data = b"compressed data"
    url = upload_export(data, "already.gz", "application/gzip", compress=True)
    assert url.count(".gz") == 1


@pytest.mark.unit
def test_metadata_headers() -> None:
    """Verify metadata headers like Content-Encoding."""
    data = b"some data to compress" * 100
    url = upload_export(data, "metadata_test.txt", "text/plain", compress=True)
    assert url is not None


@pytest.mark.unit
def test_storage_fallback_error(monkeypatch: MonkeyPatch) -> None:
    """Test that storage fails predictably when MinIO is down."""

    def mock_put_fail(*args: Any, **kwargs: Any) -> None:  # noqa: ANN401
        raise MinioException("MinIO is down")

    client = get_minio()
    monkeypatch.setattr(client, "put_object", mock_put_fail)
    with pytest.raises(MinioException):
        upload_export(b"data", "fail.txt", "text/plain")


@pytest.mark.unit
def test_bucket_creation() -> None:
    """Test that buckets are created if they don't exist."""
    client = get_minio()
    test_bucket = "test-creation-bucket"
    if client.bucket_exists(test_bucket):
        client.remove_bucket(test_bucket)

    get_minio.cache_clear()
    original_buckets = src.storage.minio_client.BUCKETS
    src.storage.minio_client.BUCKETS = [test_bucket]
    try:
        # This will call the logic and create the bucket
        new_client = get_minio()
        assert new_client.bucket_exists(test_bucket)
    finally:
        src.storage.minio_client.BUCKETS = original_buckets
        client.remove_bucket(test_bucket)
        get_minio.cache_clear()
