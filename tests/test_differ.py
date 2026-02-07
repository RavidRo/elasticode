"""Tests for the diff engine."""

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

from elasticsearch import NotFoundError

from elasticode.differ import diff_resource
from elasticode.resources.ilm_policy import IlmPolicyHandler
from elasticode.resources.index_template import IndexTemplateHandler
from elasticode.types import DesiredResource, ResourceAction, ResourceType


def _make_not_found() -> NotFoundError:
    meta = MagicMock()
    meta.status = 404
    return NotFoundError(
        "Resource not found", meta, {"error": {"type": "resource_not_found_exception"}}
    )


class TestDiffResource:
    def test_new_resource_returns_create(self, mock_es_client: MagicMock) -> None:
        mock_es_client.indices.get_index_template.side_effect = _make_not_found()
        handler = IndexTemplateHandler(mock_es_client)
        desired = DesiredResource(
            name="logs",
            resource_type=ResourceType.INDEX_TEMPLATE,
            body={"index_patterns": ["logs-*"]},
            file_path=Path("index_templates/logs.json"),
        )
        result = diff_resource(desired, handler)
        assert result.action == ResourceAction.CREATE
        assert result.current is None
        assert result.desired == {"index_patterns": ["logs-*"]}
        assert "+" in result.diff_details

    def test_identical_resource_returns_no_change(self, mock_es_client: MagicMock) -> None:
        body: dict[str, Any] = {"index_patterns": ["logs-*"], "template": {"settings": {}}}
        mock_es_client.indices.get_index_template.return_value = {
            "index_templates": [{"name": "logs", "index_template": body}]
        }
        handler = IndexTemplateHandler(mock_es_client)
        desired = DesiredResource(
            name="logs",
            resource_type=ResourceType.INDEX_TEMPLATE,
            body=body,
            file_path=Path("index_templates/logs.json"),
        )
        result = diff_resource(desired, handler)
        assert result.action == ResourceAction.NO_CHANGE
        assert result.diff_details == ""

    def test_changed_resource_returns_update(self, mock_es_client: MagicMock) -> None:
        current: dict[str, Any] = {
            "index_patterns": ["logs-*"],
            "template": {"settings": {"number_of_shards": 1}},
        }
        desired_body: dict[str, Any] = {
            "index_patterns": ["logs-*"],
            "template": {"settings": {"number_of_shards": 3}},
        }
        mock_es_client.indices.get_index_template.return_value = {
            "index_templates": [{"name": "logs", "index_template": current}]
        }
        handler = IndexTemplateHandler(mock_es_client)
        desired = DesiredResource(
            name="logs",
            resource_type=ResourceType.INDEX_TEMPLATE,
            body=desired_body,
            file_path=Path("index_templates/logs.json"),
        )
        result = diff_resource(desired, handler)
        assert result.action == ResourceAction.UPDATE
        assert "~" in result.diff_details
        assert "1" in result.diff_details
        assert "3" in result.diff_details

    def test_normalization_ignores_server_fields(self, mock_es_client: MagicMock) -> None:
        """Server-managed fields should not cause false diffs."""
        current: dict[str, Any] = {
            "policy": {"phases": {"hot": {"actions": {}}}},
            "version": 5,
            "modified_date": "2024-01-01",
            "in_use_by": {"indices": []},
        }
        desired_body: dict[str, Any] = {
            "policy": {"phases": {"hot": {"actions": {}}}},
        }
        mock_es_client.ilm.get_lifecycle.return_value = {"logs-policy": current}
        handler = IlmPolicyHandler(mock_es_client)
        desired = DesiredResource(
            name="logs-policy",
            resource_type=ResourceType.ILM_POLICY,
            body=desired_body,
            file_path=Path("ilm_policies/logs-policy.json"),
        )
        result = diff_resource(desired, handler)
        assert result.action == ResourceAction.NO_CHANGE

    def test_create_diff_contains_all_fields(self, mock_es_client: MagicMock) -> None:
        mock_es_client.indices.get_index_template.side_effect = _make_not_found()
        handler = IndexTemplateHandler(mock_es_client)
        body: dict[str, Any] = {
            "index_patterns": ["test-*"],
            "priority": 100,
        }
        desired = DesiredResource(
            name="test",
            resource_type=ResourceType.INDEX_TEMPLATE,
            body=body,
            file_path=Path("index_templates/test.json"),
        )
        result = diff_resource(desired, handler)
        assert "index_patterns" in result.diff_details
        assert "priority" in result.diff_details

    def test_update_diff_shows_added_fields(self, mock_es_client: MagicMock) -> None:
        current: dict[str, Any] = {"index_patterns": ["logs-*"]}
        desired_body: dict[str, Any] = {"index_patterns": ["logs-*"], "priority": 200}
        mock_es_client.indices.get_index_template.return_value = {
            "index_templates": [{"name": "logs", "index_template": current}]
        }
        handler = IndexTemplateHandler(mock_es_client)
        desired = DesiredResource(
            name="logs",
            resource_type=ResourceType.INDEX_TEMPLATE,
            body=desired_body,
            file_path=Path("index_templates/logs.json"),
        )
        result = diff_resource(desired, handler)
        assert result.action == ResourceAction.UPDATE
        assert "+" in result.diff_details
        assert "200" in result.diff_details
