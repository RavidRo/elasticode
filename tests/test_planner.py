"""Tests for plan generation."""

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

from elasticsearch import NotFoundError

from elasticode.planner import generate_plan
from elasticode.types import (
    AuthConfig,
    ClusterConfig,
    ElasticodeConfig,
    ResourceType,
    TlsConfig,
)


def _make_not_found() -> NotFoundError:
    meta = MagicMock()
    meta.status = 404
    return NotFoundError(
        "Resource not found", meta, {"error": {"type": "resource_not_found_exception"}}
    )


class TestGeneratePlan:
    def test_generates_plan_with_creates(
        self, fixtures_dir: Path, mock_es_client: MagicMock
    ) -> None:
        """All resources should be CREATE when nothing exists in ES."""
        mock_es_client.indices.get_index_template.side_effect = _make_not_found()
        mock_es_client.cluster.get_component_template.side_effect = _make_not_found()
        mock_es_client.ilm.get_lifecycle.side_effect = _make_not_found()
        mock_es_client.ingest.get_pipeline.side_effect = _make_not_found()

        config = ElasticodeConfig(
            clusters={
                "local": ClusterConfig(
                    url="http://localhost:9200",
                    auth=AuthConfig(type="basic", username="elastic", password="changeme"),
                    tls=TlsConfig(verify=False),
                ),
            },
            resource_dir=fixtures_dir,
        )

        plan = generate_plan(config, mock_es_client, "local")
        assert plan.cluster_name == "local"
        assert plan.has_changes
        assert len(plan.creates) == 4  # one of each type in fixtures
        assert len(plan.updates) == 0
        assert len(plan.unchanged) == 0

    def test_generates_plan_with_no_changes(
        self, fixtures_dir: Path, mock_es_client: MagicMock
    ) -> None:
        """Plan should show NO_CHANGE when ES state matches local files."""
        # Set up mock responses matching fixture content
        logs_template: dict[str, Any] = {
            "index_patterns": ["logs-*"],
            "priority": 100,
            "template": {
                "settings": {"number_of_shards": 1, "number_of_replicas": 1},
                "mappings": {
                    "properties": {
                        "@timestamp": {"type": "date"},
                        "message": {"type": "text"},
                        "level": {"type": "keyword"},
                    }
                },
            },
        }
        mock_es_client.indices.get_index_template.return_value = {
            "index_templates": [{"name": "logs-template", "index_template": logs_template}]
        }

        config = ElasticodeConfig(
            clusters={
                "local": ClusterConfig(
                    url="http://localhost:9200",
                    auth=AuthConfig(type="basic", username="elastic", password="changeme"),
                    tls=TlsConfig(verify=False),
                ),
            },
            resource_dir=fixtures_dir,
        )

        plan = generate_plan(
            config,
            mock_es_client,
            "local",
            resource_types=[ResourceType.INDEX_TEMPLATE],
        )
        assert len(plan.unchanged) == 1
        assert len(plan.creates) == 0

    def test_filter_by_resource_type(self, fixtures_dir: Path, mock_es_client: MagicMock) -> None:
        mock_es_client.ilm.get_lifecycle.side_effect = _make_not_found()

        config = ElasticodeConfig(
            clusters={
                "local": ClusterConfig(
                    url="http://localhost:9200",
                    auth=AuthConfig(type="basic", username="elastic", password="changeme"),
                    tls=TlsConfig(verify=False),
                )
            },
            resource_dir=fixtures_dir,
        )

        plan = generate_plan(
            config,
            mock_es_client,
            "local",
            resource_types=[ResourceType.ILM_POLICY],
        )
        assert len(plan.items) == 1
        assert plan.items[0].resource_type == ResourceType.ILM_POLICY

    def test_filter_by_resource_name(self, fixtures_dir: Path, mock_es_client: MagicMock) -> None:
        mock_es_client.indices.get_index_template.side_effect = _make_not_found()

        config = ElasticodeConfig(
            clusters={
                "local": ClusterConfig(
                    url="http://localhost:9200",
                    auth=AuthConfig(type="basic", username="elastic", password="changeme"),
                    tls=TlsConfig(verify=False),
                )
            },
            resource_dir=fixtures_dir,
        )

        plan = generate_plan(
            config,
            mock_es_client,
            "local",
            resource_names=["logs-template"],
        )
        assert len(plan.items) == 1
        assert plan.items[0].resource_name == "logs-template"

    def test_empty_directory_produces_empty_plan(
        self, tmp_path: Path, mock_es_client: MagicMock
    ) -> None:
        config = ElasticodeConfig(
            clusters={
                "local": ClusterConfig(
                    url="http://localhost:9200",
                    auth=AuthConfig(type="basic", username="elastic", password="changeme"),
                    tls=TlsConfig(verify=False),
                )
            },
            resource_dir=tmp_path,
        )

        plan = generate_plan(config, mock_es_client, "local")
        assert not plan.has_changes
        assert plan.items == []
