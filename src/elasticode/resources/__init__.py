"""Resource handler registry."""

from __future__ import annotations

from typing import TYPE_CHECKING

from elasticode.resources.component_template import ComponentTemplateHandler
from elasticode.resources.ilm_policy import IlmPolicyHandler
from elasticode.resources.index import IndexHandler
from elasticode.resources.index_template import IndexTemplateHandler
from elasticode.resources.ingest_pipeline import IngestPipelineHandler
from elasticode.types import ResourceType

if TYPE_CHECKING:
    from elasticsearch import Elasticsearch

    from elasticode.resources.base import ResourceHandler

HANDLER_CLASSES: dict[ResourceType, type[ResourceHandler]] = {
    ResourceType.INDEX_TEMPLATE: IndexTemplateHandler,
    ResourceType.COMPONENT_TEMPLATE: ComponentTemplateHandler,
    ResourceType.ILM_POLICY: IlmPolicyHandler,
    ResourceType.INGEST_PIPELINE: IngestPipelineHandler,
    ResourceType.INDEX: IndexHandler,
}


def get_handler(resource_type: ResourceType, client: Elasticsearch) -> ResourceHandler:
    """Get a handler instance for a given resource type."""
    handler_cls = HANDLER_CLASSES[resource_type]
    return handler_cls(client)
