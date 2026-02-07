"""Plan execution: apply changes to an Elasticsearch cluster."""

from elasticsearch import Elasticsearch
from rich.console import Console

from elasticode.errors import ApplyError
from elasticode.resources import get_handler
from elasticode.types import Plan, PlanItem, ResourceAction


def apply_plan(plan: Plan, client: Elasticsearch, console: Console) -> bool:
    """Apply a plan to the cluster. Returns True if all changes succeeded."""
    changes = [item for item in plan.items if item.action != ResourceAction.NO_CHANGE]

    if not changes:
        console.print("[green]Nothing to apply.[/green]")
        return True

    all_ok = True
    for item in changes:
        try:
            _apply_item(item, client)
            action_past = "created" if item.action == ResourceAction.CREATE else "updated"
            console.print(
                f"  [green]OK[/green]  {item.resource_type.value}/{item.resource_name} "
                f"({action_past})"
            )
        except Exception as e:
            all_ok = False
            console.print(
                f"  [red]FAIL[/red]  {item.resource_type.value}/{item.resource_name}: {e}"
            )

    return all_ok


def _apply_item(item: PlanItem, client: Elasticsearch) -> None:
    """Apply a single plan item."""
    if item.desired_body is None:
        raise ApplyError(f"No desired body for {item.resource_name}")
    handler = get_handler(item.resource_type, client)
    handler.put(item.resource_name, item.desired_body)
