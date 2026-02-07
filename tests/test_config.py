"""Tests for cluster configuration loading."""

from pathlib import Path

import pytest

from elasticode.config import interpolate_env_vars, load_config
from elasticode.errors import ConfigError


class TestInterpolateEnvVars:
    def test_replaces_single_var(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("MY_VAR", "hello")
        assert interpolate_env_vars("${MY_VAR}") == "hello"

    def test_replaces_multiple_vars(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("USER", "admin")
        monkeypatch.setenv("PASS", "secret")
        result = interpolate_env_vars("${USER}:${PASS}")
        assert result == "admin:secret"

    def test_preserves_text_without_vars(self) -> None:
        assert interpolate_env_vars("no vars here") == "no vars here"

    def test_raises_on_missing_var(self) -> None:
        with pytest.raises(ConfigError, match="not set"):
            interpolate_env_vars("${NONEXISTENT_VAR_12345}")

    def test_partial_interpolation_with_surrounding_text(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("HOST", "example.com")
        result = interpolate_env_vars("https://${HOST}:9200")
        assert result == "https://example.com:9200"


class TestLoadConfig:
    def test_load_valid_config(self, fixtures_dir: Path) -> None:
        config = load_config(fixtures_dir / "clusters.yaml")
        assert "local" in config.clusters
        assert "staging" in config.clusters
        assert config.clusters["local"].url == "http://localhost:9200"
        assert config.clusters["local"].auth.type == "basic"
        assert config.clusters["local"].auth.username == "elastic"
        assert config.clusters["staging"].auth.type == "api_key"
        assert config.clusters["staging"].auth.api_key == "test-api-key"

    def test_load_config_with_env_vars(
        self, fixtures_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("ES_USERNAME", "admin")
        monkeypatch.setenv("ES_PASSWORD", "secret123")
        config = load_config(fixtures_dir / "clusters_env_vars.yaml")
        assert config.clusters["production"].auth.username == "admin"
        assert config.clusters["production"].auth.password == "secret123"

    def test_load_missing_file_raises(self) -> None:
        with pytest.raises(ConfigError, match="Config file not found"):
            load_config("/nonexistent/path/clusters.yaml")

    def test_load_invalid_config_missing_url(self, fixtures_dir: Path) -> None:
        with pytest.raises(ConfigError, match="missing required 'url'"):
            load_config(fixtures_dir / "clusters_invalid.yaml")

    def test_load_config_missing_clusters_key(self, tmp_path: Path) -> None:
        config_file = tmp_path / "bad.yaml"
        config_file.write_text("something_else: true\n")
        with pytest.raises(ConfigError, match="must contain a 'clusters' key"):
            load_config(config_file)

    def test_tls_defaults(self, fixtures_dir: Path) -> None:
        config = load_config(fixtures_dir / "clusters.yaml")
        assert config.clusters["local"].tls.verify is False
        assert config.clusters["staging"].tls.verify is True

    def test_resource_dir_defaults_to_config_parent(self, fixtures_dir: Path) -> None:
        config = load_config(fixtures_dir / "clusters.yaml")
        assert config.resource_dir == fixtures_dir

    def test_basic_auth_missing_password(self, tmp_path: Path) -> None:
        config_file = tmp_path / "clusters.yaml"
        config_file.write_text(
            "clusters:\n"
            "  test:\n"
            "    url: http://localhost:9200\n"
            "    auth:\n"
            "      type: basic\n"
            "      username: admin\n"
        )
        with pytest.raises(ConfigError, match="requires 'username' and 'password'"):
            load_config(config_file)

    def test_api_key_auth_missing_key(self, tmp_path: Path) -> None:
        config_file = tmp_path / "clusters.yaml"
        config_file.write_text(
            "clusters:\n  test:\n    url: http://localhost:9200\n    auth:\n      type: api_key\n"
        )
        with pytest.raises(ConfigError, match="requires 'api_key'"):
            load_config(config_file)

    def test_bearer_auth_missing_token(self, tmp_path: Path) -> None:
        config_file = tmp_path / "clusters.yaml"
        config_file.write_text(
            "clusters:\n  test:\n    url: http://localhost:9200\n    auth:\n      type: bearer\n"
        )
        with pytest.raises(ConfigError, match="requires 'token'"):
            load_config(config_file)

    def test_unknown_auth_type(self, tmp_path: Path) -> None:
        config_file = tmp_path / "clusters.yaml"
        config_file.write_text(
            "clusters:\n  test:\n    url: http://localhost:9200\n    auth:\n      type: kerberos\n"
        )
        with pytest.raises(ConfigError, match="unknown auth type 'kerberos'"):
            load_config(config_file)
