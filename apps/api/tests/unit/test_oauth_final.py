from unittest.mock import MagicMock, patch

import pytest

from src.auth.oauth import get_github_user, get_google_user
from src.exceptions import AuthenticationError


@pytest.mark.unit
class TestOAuth:
    @patch("httpx.AsyncClient.post")
    @patch("httpx.AsyncClient.get")
    async def test_get_github_user_success(self, mock_get, mock_post) -> None:
        mock_post.return_value = MagicMock(status_code=200)
        mock_post.return_value.json.return_value = {"access_token": "token123"}

        mock_get.return_value = MagicMock(status_code=200)
        mock_get.return_value.json.return_value = {
            "id": 1,
            "email": "test@github.com",
            "login": "tester",
        }

        user = await get_github_user("code123")
        assert user["email"] == "test@github.com"

    @patch("httpx.AsyncClient.post")
    async def test_get_github_user_fail(self, mock_post) -> None:
        mock_post.return_value = MagicMock(status_code=400)

        with pytest.raises(AuthenticationError):
            await get_github_user("bad_code")

    @patch("httpx.AsyncClient.post")
    @patch("httpx.AsyncClient.get")
    async def test_get_google_user_success(self, mock_get, mock_post) -> None:
        mock_post.return_value = MagicMock(status_code=200)
        mock_post.return_value.json.return_value = {"access_token": "token123"}

        mock_get.return_value = MagicMock(status_code=200)
        mock_get.return_value.json.return_value = {
            "id": "g1",
            "email": "test@google.com",
            "name": "Tester",
        }

        user = await get_google_user("code123")
        assert user["email"] == "test@google.com"

    @patch("httpx.AsyncClient.post")
    async def test_get_google_user_fail(self, mock_post) -> None:
        mock_post.return_value = MagicMock(status_code=400)

        with pytest.raises(AuthenticationError):
            await get_google_user("bad_code")
