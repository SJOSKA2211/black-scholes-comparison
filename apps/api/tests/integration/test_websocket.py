import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.mark.integration
class TestWebSocketIntegration:
    def test_invalid_channel(self) -> None:
        from starlette.websockets import WebSocketDisconnect
        client = TestClient(app)
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect("/api/v1/ws/invalid_channel"):
                pass

    def test_unauthorized_ws(self) -> None:
        client = TestClient(app)
        # Without token, should fail auth
        with pytest.raises(Exception): # FastAPI TestClient raises if connection rejected
             with client.websocket_connect("/ws/experiments"):
                 pass
