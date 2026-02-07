"""Ingest pipeline resource handler."""

from typing import Any

from elasticsearch import NotFoundError

from elasticode.resources.base import ResourceHandler
from elasticode.types import ResourceType


class IngestPipelineHandler(ResourceHandler):
    """Manages Elasticsearch ingest pipelines."""

    @property
    def resource_type(self) -> ResourceType:
        return ResourceType.INGEST_PIPELINE

    @property
    def directory_name(self) -> str:
        return "ingest_pipelines"

    def get(self, name: str) -> dict[str, Any] | None:
        try:
            response = self._client.ingest.get_pipeline(id=name)
            if name in response:
                return response[name]  # type: ignore[no-any-return]
            return None
        except NotFoundError:
            return None

    def put(self, name: str, body: dict[str, Any]) -> None:
        self._client.ingest.put_pipeline(id=name, **body)

    def delete(self, name: str) -> None:
        self._client.ingest.delete_pipeline(id=name)

    def normalize(self, body: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(body)
        for key in ("version",):
            normalized.pop(key, None)
        return normalized
