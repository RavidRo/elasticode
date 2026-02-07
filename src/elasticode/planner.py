"""Plan generation: orchestrates loading resources and computing diffs."""

from elasticsearch import Elasticsearch

from elasticode.differ import diff_resource
from elasticode.loader import discover_resources
from elasticode.resources import get_handler
from elasticode.types import (
    ElasticodeConfig,
    Plan,
    PlanItem,
    ResourceAction,
    ResourceType,
)


def generate_plan(
    config: ElasticodeConfig,
    client: Elasticsearch,
    cluster_name: str,
    resource_types: list[ResourceType] | None = None,
    resource_names: list[str] | None = None,
) -> Plan:
    """Generate a plan by comparing local resources against ES cluster state."""
    desired_resources = discover_resources(
        base_dir=config.resource_dir,
        resource_types=resource_types,
        resource_names=resource_names,
    )

    items: list[PlanItem] = []

    for desired in desired_resources:
        handler = get_handler(desired.resource_type, client)
        diff = diff_resource(desired, handler)
        items.append(
            PlanItem(
                resource_name=diff.resource_name,
                resource_type=diff.resource_type,
                action=diff.action,
                desired_body=desired.body if diff.action != ResourceAction.NO_CHANGE else None,
                diff_details=diff.diff_details,
            )
        )

    return Plan(cluster_name=cluster_name, items=items)
