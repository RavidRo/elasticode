"""Index template resource handler."""

from typing import Any

from elasticsearch import NotFoundError

from elasticode.resources.base import ResourceHandler
from elasticode.types import ResourceType


class IndexTemplateHandler(ResourceHandler):
    """Manages Elasticsearch index templates."""

    @property
    def resource_type(self) -> ResourceType:
        return ResourceType.INDEX_TEMPLATE

    @property
    def directory_name(self) -> str:
        return "index_templates"

    def get(self, name: str) -> dict[str, Any] | None:
        try:
            response = self._client.indices.get_index_template(name=name)
            templates: list[dict[str, Any]] = response.get("index_templates", [])
            if templates:
                return templates[0]["index_template"]  # type: ignore[no-any-return]
            return None
        except NotFoundError:
            return None

    def put(self, name: str, body: dict[str, Any]) -> None:
        self._client.indices.put_index_template(name=name, **body)

    def delete(self, name: str) -> None:
        self._client.indices.delete_index_template(name=name)

    def normalize(self, body: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(body)
        for key in ("version",):
            normalized.pop(key, None)
        return normalized

    def list_all(self) -> dict[str, dict[str, Any]]:
        response = self._client.indices.get_index_template(name="*")
        templates: list[dict[str, Any]] = response.get("index_templates", [])
        return {t["name"]: self.normalize(t["index_template"]) for t in templates}
