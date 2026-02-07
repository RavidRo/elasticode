"""Tests for component template resource handler."""

from typing import Any
from unittest.mock import MagicMock

from elasticsearch import NotFoundError

from elasticode.resources.component_template import ComponentTemplateHandler


def _make_not_found() -> NotFoundError:
    return NotFoundError(404, "not_found", {"error": "not found"})


class TestComponentTemplateHandler:
    def test_resource_type(self, mock_es_client: MagicMock) -> None:
        handler = ComponentTemplateHandler(mock_es_client)
        assert handler.resource_type.value == "component_templates"

    def test_directory_name(self, mock_es_client: MagicMock) -> None:
        handler = ComponentTemplateHandler(mock_es_client)
        assert handler.directory_name == "component_templates"

    def test_get_returns_template_body(self, mock_es_client: MagicMock) -> None:
        template_body: dict[str, Any] = {
            "template": {"mappings": {"properties": {"host": {"type": "keyword"}}}}
        }
        mock_es_client.cluster.get_component_template.return_value = {
            "component_templates": [{"name": "base", "component_template": template_body}]
        }
        handler = ComponentTemplateHandler(mock_es_client)
        result = handler.get("base")
        assert result == template_body

    def test_get_returns_none_when_not_found(self, mock_es_client: MagicMock) -> None:
        mock_es_client.cluster.get_component_template.side_effect = _make_not_found()
        handler = ComponentTemplateHandler(mock_es_client)
        assert handler.get("nonexistent") is None

    def test_put_calls_correct_api(self, mock_es_client: MagicMock) -> None:
        handler = ComponentTemplateHandler(mock_es_client)
        body: dict[str, Any] = {"template": {"settings": {"number_of_replicas": 1}}}
        handler.put("base", body)
        mock_es_client.cluster.put_component_template.assert_called_once_with(name="base", **body)

    def test_delete_calls_correct_api(self, mock_es_client: MagicMock) -> None:
        handler = ComponentTemplateHandler(mock_es_client)
        handler.delete("base")
        mock_es_client.cluster.delete_component_template.assert_called_once_with(name="base")

    def test_normalize_strips_version(self, mock_es_client: MagicMock) -> None:
        handler = ComponentTemplateHandler(mock_es_client)
        body: dict[str, Any] = {"template": {}, "version": 5}
        result = handler.normalize(body)
        assert "version" not in result
