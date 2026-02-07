"""Tests for index resource handler."""

from typing import Any
from unittest.mock import MagicMock

import pytest
from elasticsearch import NotFoundError

from elasticode.resources.index import IndexHandler, IndexUpdateError


def _make_not_found() -> NotFoundError:
    meta = MagicMock()
    meta.status = 404
    return NotFoundError(
        "Resource not found", meta, {"error": {"type": "resource_not_found_exception"}}
    )


class TestIndexHandler:
    def test_resource_type(self, mock_es_client: MagicMock) -> None:
        handler = IndexHandler(mock_es_client)
        assert handler.resource_type.value == "indices"

    def test_directory_name(self, mock_es_client: MagicMock) -> None:
        handler = IndexHandler(mock_es_client)
        assert handler.directory_name == "indices"

    def test_get_returns_index_definition(self, mock_es_client: MagicMock) -> None:
        index_def: dict[str, Any] = {
            "settings": {"index": {"number_of_shards": "1", "number_of_replicas": "1"}},
            "mappings": {"properties": {"field1": {"type": "keyword"}}},
            "aliases": {},
        }
        mock_es_client.indices.get.return_value = {"my-index": index_def}
        handler = IndexHandler(mock_es_client)
        result = handler.get("my-index")
        assert result == index_def

    def test_get_returns_none_when_not_found(self, mock_es_client: MagicMock) -> None:
        mock_es_client.indices.get.side_effect = _make_not_found()
        handler = IndexHandler(mock_es_client)
        assert handler.get("nonexistent") is None

    def test_put_creates_new_index(self, mock_es_client: MagicMock) -> None:
        mock_es_client.indices.exists.return_value = False
        handler = IndexHandler(mock_es_client)
        body: dict[str, Any] = {
            "settings": {"number_of_shards": 1},
            "mappings": {"properties": {"field1": {"type": "text"}}},
        }
        handler.put("new-index", body)
        mock_es_client.indices.create.assert_called_once_with(index="new-index", **body)

    def test_put_raises_error_if_index_exists(self, mock_es_client: MagicMock) -> None:
        mock_es_client.indices.exists.return_value = True
        handler = IndexHandler(mock_es_client)
        body: dict[str, Any] = {"settings": {}}

        with pytest.raises(IndexUpdateError, match="already exists"):
            handler.put("existing-index", body)

        # Should not call create
        mock_es_client.indices.create.assert_not_called()

    def test_delete_raises_not_implemented(self, mock_es_client: MagicMock) -> None:
        handler = IndexHandler(mock_es_client)
        with pytest.raises(NotImplementedError, match="not supported by Elasticode for safety"):
            handler.delete("my-index")

    def test_normalize_strips_server_fields(self, mock_es_client: MagicMock) -> None:
        handler = IndexHandler(mock_es_client)
        body: dict[str, Any] = {
            "settings": {
                "index": {
                    "number_of_shards": "1",
                    "uuid": "abc123",
                    "creation_date": "1234567890",
                    "version": {"created": "8000099"},
                    "provided_name": "my-index",
                }
            },
            "mappings": {"properties": {"field1": {"type": "keyword"}}},
        }
        result = handler.normalize(body)

        # Server-managed fields should be removed
        assert "uuid" not in result["settings"]["index"]
        assert "creation_date" not in result["settings"]["index"]
        assert "version" not in result["settings"]["index"]
        assert "provided_name" not in result["settings"]["index"]

        # User-defined fields should be kept
        assert result["settings"]["index"]["number_of_shards"] == "1"
        assert result["mappings"] == {"properties": {"field1": {"type": "keyword"}}}

    def test_normalize_handles_missing_settings(self, mock_es_client: MagicMock) -> None:
        handler = IndexHandler(mock_es_client)
        body: dict[str, Any] = {"mappings": {"properties": {"field1": {"type": "text"}}}}
        result = handler.normalize(body)
        assert result == body

    def test_list_all_returns_all_indices(self, mock_es_client: MagicMock) -> None:
        mock_es_client.indices.get.return_value = {
            "index-1": {
                "settings": {"index": {"number_of_shards": "1", "uuid": "abc"}},
                "mappings": {},
            },
            "index-2": {
                "settings": {"index": {"number_of_shards": "2", "uuid": "def"}},
                "mappings": {},
            },
        }
        handler = IndexHandler(mock_es_client)
        result = handler.list_all()

        assert len(result) == 2
        assert "index-1" in result
        assert "index-2" in result

        # Should call get with wildcard
        mock_es_client.indices.get.assert_called_once_with(
            index="*", expand_wildcards="open,closed"
        )

    def test_list_all_filters_system_indices(self, mock_es_client: MagicMock) -> None:
        mock_es_client.indices.get.return_value = {
            "my-index": {"settings": {"index": {}}, "mappings": {}},
            ".kibana": {"settings": {"index": {}}, "mappings": {}},
            ".security": {"settings": {"index": {}}, "mappings": {}},
        }
        handler = IndexHandler(mock_es_client)
        result = handler.list_all()

        # System indices (starting with .) should be filtered out
        assert len(result) == 1
        assert "my-index" in result
        assert ".kibana" not in result
        assert ".security" not in result

    def test_list_all_normalizes_bodies(self, mock_es_client: MagicMock) -> None:
        mock_es_client.indices.get.return_value = {
            "my-index": {
                "settings": {"index": {"number_of_shards": "1", "uuid": "abc123"}},
                "mappings": {},
            }
        }
        handler = IndexHandler(mock_es_client)
        result = handler.list_all()

        # Should be normalized (uuid stripped)
        assert "uuid" not in result["my-index"]["settings"]["index"]

    def test_list_all_empty(self, mock_es_client: MagicMock) -> None:
        mock_es_client.indices.get.return_value = {}
        handler = IndexHandler(mock_es_client)
        assert handler.list_all() == {}
