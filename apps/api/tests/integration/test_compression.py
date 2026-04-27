import pytest
from fastapi.testclient import TestClient
from src.main import app

@pytest.mark.integration
class TestCompressionIntegration:
    def test_gzip_compression_enabled(self):
        """Verify that responses > 1000 bytes are compressed when requested."""
        client = TestClient(app)
        
        headers = {"Accept-Encoding": "gzip"}
        response = client.get("/api/openapi.json", headers=headers)
        
        assert response.status_code == 200
        # Check Content-Encoding header
        assert response.headers.get("Content-Encoding") == "gzip"

    def test_no_compression_when_not_requested(self):
        """Verify that responses are NOT compressed when identity is requested."""
        client = TestClient(app)
        # Explicitly request identity to avoid default gzip in some clients
        response = client.get("/api/openapi.json", headers={"Accept-Encoding": "identity"})
        
        assert response.status_code == 200
        assert response.headers.get("Content-Encoding") != "gzip"
