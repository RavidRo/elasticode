"""Index resource handler."""

from typing import Any

from elasticsearch import NotFoundError

from elasticode.errors import ElasticodeError
from elasticode.resources.base import ResourceHandler
from elasticode.types import ResourceType

# Fields managed by the server that should be excluded from diffs
_SERVER_MANAGED_FIELDS = (
    "creation_date",
    "uuid",
    "version",
    "provided_name",
    "routing_num_shards",
    "routing_partition_size",
    "shard",
    "store",
)


class IndexUpdateError(ElasticodeError):
    """Raised when attempting to update an existing index."""


class IndexHandler(ResourceHandler):
    """Manages Elasticsearch indices.

    IMPORTANT: This handler is create-only by default for safety.
    - Creating new indices: Allowed
    - Updating existing indices: Blocked (indices are largely immutable)
    - Deleting indices: Blocked (use Elasticsearch API directly if needed)
    """

    @property
    def resource_type(self) -> ResourceType:
        return ResourceType.INDEX

    @property
    def directory_name(self) -> str:
        return "indices"

    def get(self, name: str) -> dict[str, Any] | None:
        try:
            response = self._client.indices.get(index=name)
            if name in response:
                return response[name]  # type: ignore[no-any-return]
            return None
        except NotFoundError:
            return None

    def put(self, name: str, body: dict[str, Any]) -> None:
        # Check if index already exists
        if self._client.indices.exists(index=name):
            msg = (
                f"Index '{name}' already exists. "
                "Indices cannot be updated in-place (they are largely immutable). "
                "To modify an index, you must delete it first or use the reindex API."
            )
            raise IndexUpdateError(msg)

        # Create the index
        self._client.indices.create(index=name, **body)

    def delete(self, name: str) -> None:
        msg = (
            f"Deleting index '{name}' is not supported by Elasticode for safety. "
            "Indices contain data and deleting them is destructive. "
            "If you need to delete an index, use the Elasticsearch API directly."
        )
        raise NotImplementedError(msg)

    def normalize(self, body: dict[str, Any]) -> dict[str, Any]:
        """Normalize index definition by removing server-managed fields."""
        normalized = dict(body)

        # Normalize settings if present
        if "settings" in normalized and "index" in normalized["settings"]:
            index_settings = dict(normalized["settings"]["index"])
            for key in _SERVER_MANAGED_FIELDS:
                index_settings.pop(key, None)
            normalized["settings"] = {"index": index_settings}

        return normalized

    def list_all(self) -> dict[str, dict[str, Any]]:
        # Get all indices (excluding system indices that start with .)
        response = self._client.indices.get(index="*", expand_wildcards="open,closed")
        # Filter out system indices
        return {
            name: self.normalize(body)
            for name, body in response.items()
            if not name.startswith(".")
        }
