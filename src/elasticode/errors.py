"""Custom exception hierarchy for Elasticode."""


class ElasticodeError(Exception):
    """Base exception for all Elasticode errors."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class ConfigError(ElasticodeError):
    """Raised when cluster configuration is invalid or incomplete."""


class ValidationError(ElasticodeError):
    """Raised when resource JSON files fail validation."""


class PlanError(ElasticodeError):
    """Raised when plan generation fails."""


class ApplyError(ElasticodeError):
    """Raised when applying changes to the cluster fails."""


class ConnectionError(ElasticodeError):
    """Raised when unable to connect to the Elasticsearch cluster."""
