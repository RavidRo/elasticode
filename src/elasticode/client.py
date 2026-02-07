"""Elasticsearch client factory."""

from elasticsearch import Elasticsearch

from elasticode.errors import ConfigError
from elasticode.types import ClusterConfig


def create_client(cluster_config: ClusterConfig) -> Elasticsearch:
    """Create an Elasticsearch client from a cluster configuration."""
    kwargs: dict[str, object] = {
        "hosts": [cluster_config.url],
        "verify_certs": cluster_config.tls.verify,
    }

    if cluster_config.tls.ca_cert:
        kwargs["ca_certs"] = cluster_config.tls.ca_cert

    auth = cluster_config.auth
    if auth.type == "basic":
        kwargs["basic_auth"] = (auth.username, auth.password)
    elif auth.type == "api_key":
        kwargs["api_key"] = auth.api_key
    elif auth.type == "bearer":
        kwargs["bearer_auth"] = auth.token
    else:
        raise ConfigError(f"Unsupported auth type: {auth.type}")

    return Elasticsearch(**kwargs)  # type: ignore[arg-type]
