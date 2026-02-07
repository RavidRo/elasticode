"""Cluster configuration loading with environment variable interpolation."""

import os
import re
from pathlib import Path
from typing import Any

import yaml

from elasticode.errors import ConfigError
from elasticode.types import AuthConfig, ClusterConfig, ElasticodeConfig, TlsConfig

ENV_VAR_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")


def interpolate_env_vars(value: str) -> str:
    """Replace ${VAR_NAME} with environment variable values.

    Raises ConfigError if a referenced variable is not set.
    """

    def replacer(match: re.Match[str]) -> str:
        var_name = match.group(1)
        env_value = os.environ.get(var_name)
        if env_value is None:
            raise ConfigError(
                f"Environment variable '{var_name}' is referenced in config but not set."
            )
        return env_value

    return ENV_VAR_PATTERN.sub(replacer, value)


def _walk_and_interpolate(obj: Any) -> Any:
    """Recursively walk a data structure and interpolate env vars in strings."""
    if isinstance(obj, str):
        return interpolate_env_vars(obj)
    if isinstance(obj, dict):
        return {k: _walk_and_interpolate(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_walk_and_interpolate(item) for item in obj]
    return obj


def load_config(config_path: str | Path) -> ElasticodeConfig:
    """Load and validate clusters.yaml, returning typed config."""
    path = Path(config_path)
    if not path.exists():
        raise ConfigError(
            f"Config file not found: {path}. Run 'elasticode init' to create a starter project."
        )

    with path.open() as f:
        raw: Any = yaml.safe_load(f)

    if not isinstance(raw, dict) or "clusters" not in raw:
        raise ConfigError("Config file must contain a 'clusters' key.")

    interpolated: Any = _walk_and_interpolate(raw)
    clusters = _parse_clusters(interpolated["clusters"])
    resource_dir = Path(interpolated.get("resource_dir", path.parent))

    return ElasticodeConfig(clusters=clusters, resource_dir=resource_dir)


def _parse_clusters(raw_clusters: Any) -> dict[str, ClusterConfig]:
    """Parse and validate cluster configurations."""
    if not isinstance(raw_clusters, dict):
        raise ConfigError("'clusters' must be a mapping of cluster names to configurations.")

    clusters: dict[str, ClusterConfig] = {}
    for name, cfg in raw_clusters.items():
        if not isinstance(cfg, dict):
            raise ConfigError(f"Cluster '{name}' must be a mapping.")
        if "url" not in cfg:
            raise ConfigError(f"Cluster '{name}' missing required 'url' field.")
        auth = _parse_auth(name, cfg.get("auth", {}))
        tls = _parse_tls(cfg.get("tls", {}))
        clusters[str(name)] = ClusterConfig(url=cfg["url"], auth=auth, tls=tls)
    return clusters


def _parse_auth(cluster_name: str, raw: Any) -> AuthConfig:
    """Parse authentication configuration for a cluster."""
    if not isinstance(raw, dict):
        raise ConfigError(f"Cluster '{cluster_name}': 'auth' must be a mapping.")

    auth_type = raw.get("type", "basic")

    if auth_type == "basic":
        if "username" not in raw or "password" not in raw:
            raise ConfigError(
                f"Cluster '{cluster_name}': basic auth requires 'username' and 'password'."
            )
        return AuthConfig(type="basic", username=raw["username"], password=raw["password"])
    if auth_type == "api_key":
        if "api_key" not in raw:
            raise ConfigError(f"Cluster '{cluster_name}': api_key auth requires 'api_key'.")
        return AuthConfig(type="api_key", api_key=raw["api_key"])
    if auth_type == "bearer":
        if "token" not in raw:
            raise ConfigError(f"Cluster '{cluster_name}': bearer auth requires 'token'.")
        return AuthConfig(type="bearer", token=raw["token"])
    raise ConfigError(f"Cluster '{cluster_name}': unknown auth type '{auth_type}'.")


def _parse_tls(raw: Any) -> TlsConfig:
    """Parse TLS configuration."""
    if not isinstance(raw, dict):
        return TlsConfig()
    return TlsConfig(
        verify=raw.get("verify", True),
        ca_cert=raw.get("ca_cert"),
    )
