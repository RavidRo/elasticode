"""Rich-based terminal output formatting."""

import json
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from elasticode.types import Plan, PlanItem, ResourceAction

ACTION_STYLES: dict[ResourceAction, tuple[str, str]] = {
    ResourceAction.CREATE: ("bold green", "+"),
    ResourceAction.UPDATE: ("bold yellow", "~"),
    ResourceAction.NO_CHANGE: ("dim", " "),
}


def display_plan(plan: Plan, console: Console) -> None:
    """Render a plan to the terminal with colored output."""
    if not plan.has_changes:
        console.print(
            Panel(
                "[green]No changes.[/green] Your resources match the cluster state.",
                title=f"Plan: {plan.cluster_name}",
            )
        )
        return

    console.print(f"\n[bold]Plan for cluster:[/bold] [cyan]{plan.cluster_name}[/cyan]\n")

    # Summary table
    table = Table(title="Change Summary")
    table.add_column("Action", style="bold")
    table.add_column("Count", justify="right")
    table.add_row("[green]Create[/green]", str(len(plan.creates)))
    table.add_row("[yellow]Update[/yellow]", str(len(plan.updates)))
    table.add_row("[dim]Unchanged[/dim]", str(len(plan.unchanged)))
    console.print(table)
    console.print()

    # Detailed changes
    for item in plan.items:
        if item.action == ResourceAction.NO_CHANGE:
            continue
        _display_plan_item(item, console)

    console.print(
        f"\n[bold]Total:[/bold] {len(plan.creates)} to create, "
        f"{len(plan.updates)} to update, {len(plan.unchanged)} unchanged.\n"
    )


def display_plan_json(plan: Plan, console: Console) -> None:
    """Render a plan as JSON output."""
    data: dict[str, Any] = {
        "cluster": plan.cluster_name,
        "summary": {
            "creates": len(plan.creates),
            "updates": len(plan.updates),
            "unchanged": len(plan.unchanged),
        },
        "items": [
            {
                "name": item.resource_name,
                "type": item.resource_type.value,
                "action": item.action.value,
            }
            for item in plan.items
            if item.action != ResourceAction.NO_CHANGE
        ],
    }
    console.print(json.dumps(data, indent=2))


def _display_plan_item(item: PlanItem, console: Console) -> None:
    """Display a single plan item with colored diff."""
    style, symbol = ACTION_STYLES[item.action]
    resource_label = f"{item.resource_type.value}/{item.resource_name}"
    console.print(f"  [{style}]{symbol} {resource_label}[/{style}]")
    if item.diff_details:
        for line in item.diff_details.splitlines():
            stripped = line.strip()
            if stripped.startswith("+"):
                console.print(f"      [green]{line}[/green]")
            elif stripped.startswith("-"):
                console.print(f"      [red]{line}[/red]")
            elif stripped.startswith("~"):
                console.print(f"      [yellow]{line}[/yellow]")
            else:
                console.print(f"      {line}")
    console.print()
