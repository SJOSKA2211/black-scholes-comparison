"""Integration tests for MinIO storage.
Strictly zero-mock: uses real MinIO instance.
"""

import io
import pytest
from src.storage.minio_client import get_minio
from src.storage.storage_service import upload_export

@pytest.mark.integration
class TestStorageIntegration:
    def test_minio_bucket_lifecycle(self):
        """Test bucket existence and object upload/download."""
        client = get_minio()
        bucket = "integration-test-bucket"
        
        # 1. Bucket creation
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)
        assert client.bucket_exists(bucket)
        
        # 2. Object upload
        content = b"hello integration world"
        obj_name = "test_file.txt"
        client.put_object(
            bucket, obj_name, io.BytesIO(content), length=len(content),
            content_type="text/plain"
        )
        
        # 3. Object retrieval
        response = client.get_object(bucket, obj_name)
        try:
            retrieved = response.read()
            assert retrieved == content
        finally:
            response.close()
            response.release_conn()
            
        # 4. Cleanup
        client.remove_object(bucket, obj_name)
        client.remove_bucket(bucket)
        assert not client.bucket_exists(bucket)

    def test_storage_service_upload_flow(self):
        """Test the high-level upload_export service."""
        content = b"export data"
        filename = "export_test.txt"
        
        url = upload_export(content, filename, "text/plain", compress=False)
        assert "http" in url
        assert "bs-exports" in url or "9000" in url

    def test_storage_service_compression(self):
        """Test that large files are compressed in MinIO."""
        from src.utils.compression import decompress_data
        
        # Data > 1KB to trigger compression
        content = b"Repeatable data " * 100 
        filename = "compression_test.txt"
        
        url = upload_export(content, filename, "text/plain")
        assert ".gz" in url
        
        # Verify directly via MinIO client
        client = get_minio()
        # Find the object name from the URL or reconstruct it
        # upload_export uses: exports/%Y/%m/%d/filename.gz
        import datetime
        date_path = datetime.datetime.now(datetime.UTC).strftime("%Y/%m/%d")
        obj_name = f"exports/{date_path}/{filename}.gz"
        
        stat = client.stat_object("bs-exports", obj_name)
        assert stat.metadata.get("Content-Encoding") == "gzip"
        assert stat.size < len(content)
        
        # Retrieve
        # MinIO client (urllib3) might auto-decompress if it sees Content-Encoding: gzip
        response = client.get_object("bs-exports", obj_name)
        try:
            retrieved = response.read()
            # If auto-decompressed, it should match original content
            # If not, we decompress manually
            if retrieved != content:
                retrieved = decompress_data(retrieved, method="gzip")
            assert retrieved == content
        finally:
            response.close()
            response.release_conn()
