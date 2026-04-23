"""Unit tests for additional experiments router coverage."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


@pytest.mark.unit
class TestExperimentsRouterCoverage:
    @patch("src.auth.dependencies.get_supabase_client")
    @patch("src.routers.experiments.publish_experiment_task")
    def test_run_experiment_exception(self, mock_publish, mock_get_supabase) -> None:
        """Test exception handling in run_experiment."""
        mock_supabase = MagicMock()
        mock_get_supabase.return_value = mock_supabase
        mock_user = MagicMock()
        mock_user.id = "user-1"
        mock_supabase.auth.get_user.return_value = MagicMock(user=mock_user)
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"role": "researcher"}]
        )

        mock_publish.side_effect = Exception("Queue full")

        response = client.post(
            "/api/v1/experiments/run",
            json={"params": {}},
            headers={"Authorization": "Bearer token"},
        )
        assert response.status_code == 500
        assert "Failed to submit experiment" in response.json()["detail"]

    @patch("src.auth.dependencies.get_supabase_client")
    @patch("src.routers.experiments.get_experiments_by_method")
    def test_get_results_by_method(self, mock_get_by_method, mock_get_supabase) -> None:
        """Test fetching results by method."""
        mock_supabase = MagicMock()
        mock_get_supabase.return_value = mock_supabase
        mock_user = MagicMock()
        mock_supabase.auth.get_user.return_value = MagicMock(user=mock_user)
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"role": "researcher"}]
        )

        mock_get_by_method.return_value = [{"id": "1"}]

        response = client.get(
            "/api/v1/experiments/results?method_type=analytical",
            headers={"Authorization": "Bearer token"},
        )
        assert response.status_code == 200
        assert response.json() == [{"id": "1"}]

    @patch("src.auth.dependencies.get_supabase_client")
    @patch("src.routers.experiments.get_experiments")
    def test_get_results_exception(self, mock_get_experiments, mock_get_supabase) -> None:
        """Test exception handling in get_results."""
        mock_supabase = MagicMock()
        mock_get_supabase.return_value = mock_supabase
        mock_user = MagicMock()
        mock_supabase.auth.get_user.return_value = MagicMock(user=mock_user)
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"role": "researcher"}]
        )

        mock_get_experiments.side_effect = Exception("DB error")

        response = client.get(
            "/api/v1/experiments/results", headers={"Authorization": "Bearer token"}
        )
        assert response.status_code == 500
        assert "Failed to fetch results" in response.json()["detail"]

    @patch("src.auth.dependencies.get_supabase_client")
    @patch("src.routers.experiments.get_experiment_by_id")
    def test_get_result_detail_flow(self, mock_get_by_id, mock_get_supabase) -> None:
        """Test successful and missing result detail."""
        mock_supabase = MagicMock()
        mock_get_supabase.return_value = mock_supabase
        mock_user = MagicMock()
        mock_supabase.auth.get_user.return_value = MagicMock(user=mock_user)
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"role": "researcher"}]
        )

        # Success
        mock_get_by_id.return_value = {"id": "exp-1"}
        response = client.get(
            "/api/v1/experiments/results/exp-1", headers={"Authorization": "Bearer token"}
        )
        assert response.status_code == 200

        # Not found
        mock_get_by_id.return_value = None
        response = client.get(
            "/api/v1/experiments/results/missing", headers={"Authorization": "Bearer token"}
        )
        assert response.status_code == 404

        # Exception
        mock_get_by_id.side_effect = Exception("Internal")
        response = client.get(
            "/api/v1/experiments/results/error", headers={"Authorization": "Bearer token"}
        )
        assert response.status_code == 500
