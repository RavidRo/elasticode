"""Shared test fixtures for Elasticode."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from click.testing import CliRunner

from elasticode.types import AuthConfig, ClusterConfig, ElasticodeConfig, TlsConfig

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES_DIR


@pytest.fixture
def cli_runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def mock_es_client() -> MagicMock:
    """A mock Elasticsearch client with pre-configured sub-clients."""
    client = MagicMock()
    client.indices = MagicMock()
    client.cluster = MagicMock()
    client.ilm = MagicMock()
    client.ingest = MagicMock()
    return client


@pytest.fixture
def sample_cluster_config() -> ClusterConfig:
    return ClusterConfig(
        url="http://localhost:9200",
        auth=AuthConfig(type="basic", username="elastic", password="changeme"),
        tls=TlsConfig(verify=False),
    )


@pytest.fixture
def sample_config(fixtures_dir: Path) -> ElasticodeConfig:
    return ElasticodeConfig(
        clusters={
            "local": ClusterConfig(
                url="http://localhost:9200",
                auth=AuthConfig(type="basic", username="elastic", password="changeme"),
                tls=TlsConfig(verify=False),
            ),
        },
        resource_dir=fixtures_dir,
    )
