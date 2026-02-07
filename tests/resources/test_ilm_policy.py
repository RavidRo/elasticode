"""Tests for ILM policy resource handler."""

from typing import Any
from unittest.mock import MagicMock

from elasticsearch import NotFoundError

from elasticode.resources.ilm_policy import IlmPolicyHandler


def _make_not_found() -> NotFoundError:
    meta = MagicMock()
    meta.status = 404
    return NotFoundError(
        "Resource not found", meta, {"error": {"type": "resource_not_found_exception"}}
    )


class TestIlmPolicyHandler:
    def test_resource_type(self, mock_es_client: MagicMock) -> None:
        handler = IlmPolicyHandler(mock_es_client)
        assert handler.resource_type.value == "ilm_policies"

    def test_directory_name(self, mock_es_client: MagicMock) -> None:
        handler = IlmPolicyHandler(mock_es_client)
        assert handler.directory_name == "ilm_policies"

    def test_get_returns_policy_body(self, mock_es_client: MagicMock) -> None:
        policy_body: dict[str, Any] = {
            "policy": {"phases": {"hot": {"actions": {"rollover": {"max_age": "30d"}}}}}
        }
        mock_es_client.ilm.get_lifecycle.return_value = {"logs-policy": policy_body}
        handler = IlmPolicyHandler(mock_es_client)
        result = handler.get("logs-policy")
        assert result == policy_body

    def test_get_returns_none_when_not_found(self, mock_es_client: MagicMock) -> None:
        mock_es_client.ilm.get_lifecycle.side_effect = _make_not_found()
        handler = IlmPolicyHandler(mock_es_client)
        assert handler.get("nonexistent") is None

    def test_get_returns_none_when_name_not_in_response(self, mock_es_client: MagicMock) -> None:
        mock_es_client.ilm.get_lifecycle.return_value = {"other-policy": {}}
        handler = IlmPolicyHandler(mock_es_client)
        assert handler.get("logs-policy") is None

    def test_put_calls_correct_api(self, mock_es_client: MagicMock) -> None:
        handler = IlmPolicyHandler(mock_es_client)
        body: dict[str, Any] = {
            "policy": {"phases": {"delete": {"min_age": "90d", "actions": {"delete": {}}}}}
        }
        handler.put("logs-policy", body)
        mock_es_client.ilm.put_lifecycle.assert_called_once_with(name="logs-policy", **body)

    def test_delete_calls_correct_api(self, mock_es_client: MagicMock) -> None:
        handler = IlmPolicyHandler(mock_es_client)
        handler.delete("logs-policy")
        mock_es_client.ilm.delete_lifecycle.assert_called_once_with(name="logs-policy")

    def test_normalize_strips_server_managed_fields(self, mock_es_client: MagicMock) -> None:
        handler = IlmPolicyHandler(mock_es_client)
        body: dict[str, Any] = {
            "policy": {"phases": {}},
            "version": 2,
            "modified_date": "2024-01-01",
            "modified_date_millis": 1704067200000,
            "in_use_by": {"indices": ["logs-000001"]},
        }
        result = handler.normalize(body)
        assert "version" not in result
        assert "modified_date" not in result
        assert "modified_date_millis" not in result
        assert "in_use_by" not in result
        assert "policy" in result

    def test_list_all_returns_all_policies(self, mock_es_client: MagicMock) -> None:
        mock_es_client.ilm.get_lifecycle.return_value = {
            "logs-policy": {"policy": {"phases": {"hot": {"actions": {}}}}},
            "metrics-policy": {"policy": {"phases": {"delete": {"min_age": "90d"}}}},
        }
        handler = IlmPolicyHandler(mock_es_client)
        result = handler.list_all()
        assert len(result) == 2
        assert "logs-policy" in result
        assert "metrics-policy" in result

    def test_list_all_empty(self, mock_es_client: MagicMock) -> None:
        mock_es_client.ilm.get_lifecycle.return_value = {}
        handler = IlmPolicyHandler(mock_es_client)
        assert handler.list_all() == {}

    def test_list_all_normalizes_bodies(self, mock_es_client: MagicMock) -> None:
        mock_es_client.ilm.get_lifecycle.return_value = {
            "logs-policy": {
                "policy": {"phases": {}},
                "version": 2,
                "modified_date": "2024-01-01",
                "in_use_by": {"indices": []},
            }
        }
        handler = IlmPolicyHandler(mock_es_client)
        result = handler.list_all()
        assert "version" not in result["logs-policy"]
        assert "modified_date" not in result["logs-policy"]
        assert "in_use_by" not in result["logs-policy"]
