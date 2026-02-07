"""Tests for the export module."""

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from elasticode.errors import ExportError
from elasticode.exporter import export_resources
from elasticode.types import ResourceType


@pytest.fixture
def _mock_handlers(mock_es_client: MagicMock) -> None:
    """Set up mock handlers to return sample resources for all types."""
    # Index templates
    mock_es_client.indices.get_index_template.return_value = {
        "index_templates": [
            {
                "name": "logs",
                "index_template": {"index_patterns": ["logs-*"], "version": 1},
            }
        ]
    }
    # Component templates
    mock_es_client.cluster.get_component_template.return_value = {
        "component_templates": [
            {
                "name": "base-settings",
                "component_template": {"template": {"settings": {}}, "version": 2},
            }
        ]
    }
    # ILM policies
    mock_es_client.ilm.get_lifecycle.return_value = {
        "logs-policy": {
            "policy": {"phases": {"hot": {"actions": {}}}},
            "version": 3,
            "modified_date": "2024-01-01",
        }
    }
    # Ingest pipelines
    mock_es_client.ingest.get_pipeline.return_value = {
        "parse-logs": {"description": "Parse logs", "processors": [], "version": 4}
    }


class TestExportResources:
    @pytest.mark.usefixtures("_mock_handlers")
    def test_export_all_resource_types(self, mock_es_client: MagicMock, tmp_path: Path) -> None:
        result = export_resources(mock_es_client, "local", tmp_path)

        assert result.exported_count == 4
        assert result.skipped_count == 0
        assert (tmp_path / "index_templates" / "logs.json").exists()
        assert (tmp_path / "component_templates" / "base-settings.json").exists()
        assert (tmp_path / "ilm_policies" / "logs-policy.json").exists()
        assert (tmp_path / "ingest_pipelines" / "parse-logs.json").exists()

    @pytest.mark.usefixtures("_mock_handlers")
    def test_export_filters_by_resource_type(
        self, mock_es_client: MagicMock, tmp_path: Path
    ) -> None:
        result = export_resources(
            mock_es_client, "local", tmp_path, resource_types=[ResourceType.ILM_POLICY]
        )

        assert result.exported_count == 1
        assert (tmp_path / "ilm_policies" / "logs-policy.json").exists()
        assert not (tmp_path / "index_templates").exists()

    @pytest.mark.usefixtures("_mock_handlers")
    def test_export_filters_by_resource_name(
        self, mock_es_client: MagicMock, tmp_path: Path
    ) -> None:
        result = export_resources(mock_es_client, "local", tmp_path, resource_names=["logs"])

        assert result.exported_count == 1
        assert (tmp_path / "index_templates" / "logs.json").exists()

    @pytest.mark.usefixtures("_mock_handlers")
    def test_export_skips_existing_files(self, mock_es_client: MagicMock, tmp_path: Path) -> None:
        # Pre-create a file
        (tmp_path / "index_templates").mkdir(parents=True)
        (tmp_path / "index_templates" / "logs.json").write_text("{}")

        result = export_resources(mock_es_client, "local", tmp_path)

        assert result.skipped_count == 1
        assert result.skipped[0] == (ResourceType.INDEX_TEMPLATE, "logs", "file already exists")
        # File should still have original content
        assert (tmp_path / "index_templates" / "logs.json").read_text() == "{}"

    @pytest.mark.usefixtures("_mock_handlers")
    def test_export_force_overwrites_existing(
        self, mock_es_client: MagicMock, tmp_path: Path
    ) -> None:
        # Pre-create a file with old content
        (tmp_path / "index_templates").mkdir(parents=True)
        (tmp_path / "index_templates" / "logs.json").write_text("{}")

        result = export_resources(mock_es_client, "local", tmp_path, force=True)

        assert result.skipped_count == 0
        content = json.loads((tmp_path / "index_templates" / "logs.json").read_text())
        assert content == {"index_patterns": ["logs-*"]}

    @pytest.mark.usefixtures("_mock_handlers")
    def test_export_creates_subdirectories(self, mock_es_client: MagicMock, tmp_path: Path) -> None:
        output_dir = tmp_path / "nested" / "output"
        result = export_resources(
            mock_es_client, "local", output_dir, resource_types=[ResourceType.INDEX_TEMPLATE]
        )

        assert result.exported_count == 1
        assert (output_dir / "index_templates" / "logs.json").exists()

    @pytest.mark.usefixtures("_mock_handlers")
    def test_export_writes_formatted_json(self, mock_es_client: MagicMock, tmp_path: Path) -> None:
        export_resources(
            mock_es_client, "local", tmp_path, resource_types=[ResourceType.INDEX_TEMPLATE]
        )

        content = (tmp_path / "index_templates" / "logs.json").read_text()
        # Should be indented and end with newline
        assert "  " in content
        assert content.endswith("\n")
        # Should be valid JSON without server fields
        parsed = json.loads(content)
        assert "version" not in parsed

    def test_export_handles_empty_cluster(self, mock_es_client: MagicMock, tmp_path: Path) -> None:
        mock_es_client.indices.get_index_template.return_value = {"index_templates": []}
        mock_es_client.cluster.get_component_template.return_value = {"component_templates": []}
        mock_es_client.ilm.get_lifecycle.return_value = {}
        mock_es_client.ingest.get_pipeline.return_value = {}

        result = export_resources(mock_es_client, "local", tmp_path)

        assert result.exported_count == 0
        assert result.skipped_count == 0

    def test_export_raises_export_error_on_api_failure(
        self, mock_es_client: MagicMock, tmp_path: Path
    ) -> None:
        mock_es_client.indices.get_index_template.side_effect = RuntimeError("connection lost")

        with pytest.raises(ExportError, match="Failed to list"):
            export_resources(
                mock_es_client,
                "local",
                tmp_path,
                resource_types=[ResourceType.INDEX_TEMPLATE],
            )
