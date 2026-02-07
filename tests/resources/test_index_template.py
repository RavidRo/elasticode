"""Tests for index template resource handler."""

from typing import Any
from unittest.mock import MagicMock

from elasticsearch import NotFoundError

from elasticode.resources.index_template import IndexTemplateHandler


def _make_not_found() -> NotFoundError:
    # Create a minimal mock for ApiResponseMeta
    meta = MagicMock()
    meta.status = 404
    return NotFoundError(
        "Resource not found", meta, {"error": {"type": "resource_not_found_exception"}}
    )


class TestIndexTemplateHandler:
    def test_resource_type(self, mock_es_client: MagicMock) -> None:
        handler = IndexTemplateHandler(mock_es_client)
        assert handler.resource_type.value == "index_templates"

    def test_directory_name(self, mock_es_client: MagicMock) -> None:
        handler = IndexTemplateHandler(mock_es_client)
        assert handler.directory_name == "index_templates"

    def test_get_returns_template_body(self, mock_es_client: MagicMock) -> None:
        template_body: dict[str, Any] = {"index_patterns": ["logs-*"]}
        mock_es_client.indices.get_index_template.return_value = {
            "index_templates": [{"name": "logs", "index_template": template_body}]
        }
        handler = IndexTemplateHandler(mock_es_client)
        result = handler.get("logs")
        assert result == template_body
        mock_es_client.indices.get_index_template.assert_called_once_with(name="logs")

    def test_get_returns_none_when_not_found(self, mock_es_client: MagicMock) -> None:
        mock_es_client.indices.get_index_template.side_effect = _make_not_found()
        handler = IndexTemplateHandler(mock_es_client)
        assert handler.get("nonexistent") is None

    def test_get_returns_none_for_empty_list(self, mock_es_client: MagicMock) -> None:
        mock_es_client.indices.get_index_template.return_value = {"index_templates": []}
        handler = IndexTemplateHandler(mock_es_client)
        assert handler.get("empty") is None

    def test_put_calls_correct_api(self, mock_es_client: MagicMock) -> None:
        handler = IndexTemplateHandler(mock_es_client)
        body: dict[str, Any] = {
            "index_patterns": ["logs-*"],
            "template": {"settings": {"number_of_shards": 1}},
        }
        handler.put("logs", body)
        mock_es_client.indices.put_index_template.assert_called_once_with(name="logs", **body)

    def test_delete_calls_correct_api(self, mock_es_client: MagicMock) -> None:
        handler = IndexTemplateHandler(mock_es_client)
        handler.delete("logs")
        mock_es_client.indices.delete_index_template.assert_called_once_with(name="logs")

    def test_normalize_strips_version(self, mock_es_client: MagicMock) -> None:
        handler = IndexTemplateHandler(mock_es_client)
        body: dict[str, Any] = {"index_patterns": ["logs-*"], "version": 3}
        result = handler.normalize(body)
        assert "version" not in result
        assert result["index_patterns"] == ["logs-*"]

    def test_normalize_preserves_other_fields(self, mock_es_client: MagicMock) -> None:
        handler = IndexTemplateHandler(mock_es_client)
        body: dict[str, Any] = {
            "index_patterns": ["logs-*"],
            "template": {"settings": {}},
            "priority": 100,
        }
        result = handler.normalize(body)
        assert result == body
