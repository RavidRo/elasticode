"""ILM policy resource handler."""

from typing import Any

from elasticsearch import NotFoundError

from elasticode.resources.base import ResourceHandler
from elasticode.types import ResourceType

# Fields managed by the server that should be excluded from diffs
_SERVER_MANAGED_FIELDS = ("version", "modified_date", "modified_date_millis", "in_use_by")


class IlmPolicyHandler(ResourceHandler):
    """Manages Elasticsearch ILM (Index Lifecycle Management) policies."""

    @property
    def resource_type(self) -> ResourceType:
        return ResourceType.ILM_POLICY

    @property
    def directory_name(self) -> str:
        return "ilm_policies"

    def get(self, name: str) -> dict[str, Any] | None:
        try:
            response = self._client.ilm.get_lifecycle(name=name)
            if name in response:
                return response[name]  # type: ignore[no-any-return]
            return None
        except NotFoundError:
            return None

    def put(self, name: str, body: dict[str, Any]) -> None:
        self._client.ilm.put_lifecycle(name=name, **body)

    def delete(self, name: str) -> None:
        self._client.ilm.delete_lifecycle(name=name)

    def normalize(self, body: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(body)
        for key in _SERVER_MANAGED_FIELDS:
            normalized.pop(key, None)
        return normalized
