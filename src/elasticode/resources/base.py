"""Abstract base class for Elasticsearch resource handlers."""

from abc import ABC, abstractmethod
from typing import Any

from elasticsearch import Elasticsearch

from elasticode.types import ResourceType


class ResourceHandler(ABC):
    """Abstract base for managing a specific Elasticsearch resource type."""

    def __init__(self, client: Elasticsearch) -> None:
        self._client = client

    @property
    @abstractmethod
    def resource_type(self) -> ResourceType:
        """The ResourceType enum value this handler manages."""
        ...

    @property
    @abstractmethod
    def directory_name(self) -> str:
        """The directory name where resource JSON files live."""
        ...

    @abstractmethod
    def get(self, name: str) -> dict[str, Any] | None:
        """Fetch a resource by name from ES. Returns None if not found."""
        ...

    @abstractmethod
    def put(self, name: str, body: dict[str, Any]) -> None:
        """Create or update a resource."""
        ...

    @abstractmethod
    def delete(self, name: str) -> None:
        """Delete a resource by name."""
        ...

    @abstractmethod
    def normalize(self, body: dict[str, Any]) -> dict[str, Any]:
        """Normalize a resource body for comparison.

        Strips server-managed fields that should not be included in diffs.
        """
        ...
