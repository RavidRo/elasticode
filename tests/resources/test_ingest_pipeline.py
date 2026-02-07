"""Tests for ingest pipeline resource handler."""

from typing import Any
from unittest.mock import MagicMock

from elasticsearch import NotFoundError

from elasticode.resources.ingest_pipeline import IngestPipelineHandler


def _make_not_found() -> NotFoundError:
    meta = MagicMock()
    meta.status = 404
    return NotFoundError(
        "Resource not found", meta, {"error": {"type": "resource_not_found_exception"}}
    )


class TestIngestPipelineHandler:
    def test_resource_type(self, mock_es_client: MagicMock) -> None:
        handler = IngestPipelineHandler(mock_es_client)
        assert handler.resource_type.value == "ingest_pipelines"

    def test_directory_name(self, mock_es_client: MagicMock) -> None:
        handler = IngestPipelineHandler(mock_es_client)
        assert handler.directory_name == "ingest_pipelines"

    def test_get_returns_pipeline_body(self, mock_es_client: MagicMock) -> None:
        pipeline_body: dict[str, Any] = {
            "description": "Parse logs",
            "processors": [{"grok": {"field": "message", "patterns": ["%{GREEDYDATA:msg}"]}}],
        }
        mock_es_client.ingest.get_pipeline.return_value = {"parse-logs": pipeline_body}
        handler = IngestPipelineHandler(mock_es_client)
        result = handler.get("parse-logs")
        assert result == pipeline_body

    def test_get_returns_none_when_not_found(self, mock_es_client: MagicMock) -> None:
        mock_es_client.ingest.get_pipeline.side_effect = _make_not_found()
        handler = IngestPipelineHandler(mock_es_client)
        assert handler.get("nonexistent") is None

    def test_put_calls_correct_api(self, mock_es_client: MagicMock) -> None:
        handler = IngestPipelineHandler(mock_es_client)
        body: dict[str, Any] = {"description": "test", "processors": []}
        handler.put("test-pipeline", body)
        mock_es_client.ingest.put_pipeline.assert_called_once_with(id="test-pipeline", **body)

    def test_delete_calls_correct_api(self, mock_es_client: MagicMock) -> None:
        handler = IngestPipelineHandler(mock_es_client)
        handler.delete("test-pipeline")
        mock_es_client.ingest.delete_pipeline.assert_called_once_with(id="test-pipeline")

    def test_normalize_strips_version(self, mock_es_client: MagicMock) -> None:
        handler = IngestPipelineHandler(mock_es_client)
        body: dict[str, Any] = {"description": "test", "processors": [], "version": 4}
        result = handler.normalize(body)
        assert "version" not in result
        assert result["description"] == "test"

    def test_list_all_returns_all_pipelines(self, mock_es_client: MagicMock) -> None:
        mock_es_client.ingest.get_pipeline.return_value = {
            "parse-logs": {"description": "Parse", "processors": []},
            "enrich-data": {"description": "Enrich", "processors": []},
        }
        handler = IngestPipelineHandler(mock_es_client)
        result = handler.list_all()
        assert len(result) == 2
        assert "parse-logs" in result
        assert "enrich-data" in result

    def test_list_all_empty(self, mock_es_client: MagicMock) -> None:
        mock_es_client.ingest.get_pipeline.return_value = {}
        handler = IngestPipelineHandler(mock_es_client)
        assert handler.list_all() == {}

    def test_list_all_normalizes_bodies(self, mock_es_client: MagicMock) -> None:
        mock_es_client.ingest.get_pipeline.return_value = {
            "parse-logs": {"description": "Parse", "processors": [], "version": 4}
        }
        handler = IngestPipelineHandler(mock_es_client)
        result = handler.list_all()
        assert "version" not in result["parse-logs"]
