"""Component template resource handler."""

from typing import Any

from elasticsearch import NotFoundError

from elasticode.resources.base import ResourceHandler
from elasticode.types import ResourceType


class ComponentTemplateHandler(ResourceHandler):
    """Manages Elasticsearch component templates."""

    @property
    def resource_type(self) -> ResourceType:
        return ResourceType.COMPONENT_TEMPLATE

    @property
    def directory_name(self) -> str:
        return "component_templates"

    def get(self, name: str) -> dict[str, Any] | None:
        try:
            response = self._client.cluster.get_component_template(name=name)
            templates: list[dict[str, Any]] = response.get("component_templates", [])
            if templates:
                return templates[0]["component_template"]  # type: ignore[no-any-return]
            return None
        except NotFoundError:
            return None

    def put(self, name: str, body: dict[str, Any]) -> None:
        self._client.cluster.put_component_template(name=name, **body)

    def delete(self, name: str) -> None:
        self._client.cluster.delete_component_template(name=name)

    def normalize(self, body: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(body)
        for key in ("version",):
            normalized.pop(key, None)
        return normalized
