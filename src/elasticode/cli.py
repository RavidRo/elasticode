"""Elasticode CLI: declaratively manage Elasticsearch 8.x resources."""

from pathlib import Path

import click
from rich.console import Console

from elasticode.applier import apply_plan
from elasticode.client import create_client
from elasticode.config import load_config
from elasticode.errors import ElasticodeError
from elasticode.loader import validate_resources
from elasticode.output import display_plan, display_plan_json
from elasticode.planner import generate_plan
from elasticode.scaffold import scaffold_project
from elasticode.types import ResourceType

RESOURCE_TYPE_CHOICES = [rt.value for rt in ResourceType]
RESOURCE_TYPE_MAP = {rt.value: rt for rt in ResourceType}


@click.group()
@click.option(
    "--config",
    "-c",
    type=click.Path(),
    default="clusters.yaml",
    help="Path to clusters.yaml config file.",
)
@click.option("--quiet", "-q", is_flag=True, help="Suppress non-essential output.")
@click.option("--no-color", is_flag=True, help="Disable colored output.")
@click.version_option(package_name="elasticode")
@click.pass_context
def main(ctx: click.Context, config: str, quiet: bool, no_color: bool) -> None:
    """Elasticode: Declaratively manage Elasticsearch 8.x resources."""
    ctx.ensure_object(dict)
    ctx.obj["config_path"] = config
    ctx.obj["quiet"] = quiet
    ctx.obj["no_color"] = no_color


@main.command()
@click.option(
    "--directory",
    "-d",
    type=click.Path(),
    default=".",
    help="Directory to scaffold the project in.",
)
def init(directory: str) -> None:
    """Scaffold a new Elasticode project with example files."""
    console = Console()
    target = Path(directory).resolve()

    created = scaffold_project(target)

    if not created:
        console.print("[yellow]Project already exists.[/yellow] No files were created.")
        return

    console.print(f"[green]Project initialized in {target}[/green]\n")
    console.print("Created:")
    for path in created:
        relative = path.relative_to(target)
        if path.is_dir():
            console.print(f"  [blue]{relative}/[/blue]")
        else:
            console.print(f"  {relative}")
    console.print(
        "\n[dim]Next steps:[/dim]\n"
        "  1. Edit clusters.yaml with your cluster details\n"
        "  2. Add resource JSON files to the appropriate directories\n"
        "  3. Run [bold]elasticode validate[/bold] to check your files\n"
        "  4. Run [bold]elasticode plan --cluster <name>[/bold] to preview changes\n"
        "  5. Run [bold]elasticode apply --cluster <name>[/bold] to apply changes"
    )


@main.command()
@click.option(
    "--resource-type",
    "-t",
    multiple=True,
    type=click.Choice(RESOURCE_TYPE_CHOICES),
    help="Filter by resource type (repeatable).",
)
@click.option(
    "--resource",
    "-r",
    multiple=True,
    help="Filter by specific resource name (repeatable).",
)
@click.pass_context
def validate(ctx: click.Context, resource_type: tuple[str, ...], resource: tuple[str, ...]) -> None:
    """Validate JSON resource files and cluster configuration."""
    console = Console(no_color=ctx.obj.get("no_color", False))

    try:
        config = load_config(ctx.obj["config_path"])
        console.print(f"  [green]OK[/green]  clusters.yaml ({len(config.clusters)} cluster(s))")

        rtypes = [RESOURCE_TYPE_MAP[rt] for rt in resource_type] if resource_type else None
        rnames = list(resource) if resource else None

        errors = validate_resources(config.resource_dir, rtypes, rnames)
        if errors:
            for err in errors:
                console.print(f"  [red]ERROR[/red]  {err}")
            raise SystemExit(1)

        # Count valid resources
        from elasticode.loader import discover_resources

        resources = discover_resources(config.resource_dir, rtypes, rnames)
        for res in resources:
            console.print(f"  [green]OK[/green]  {res.resource_type.value}/{res.name}")

        console.print(f"\n[green]All {len(resources)} resource(s) valid.[/green]")

    except ElasticodeError as e:
        console.print(f"[red]Error:[/red] {e.message}")
        raise SystemExit(1) from None


@main.command()
@click.option("--cluster", required=True, help="Target cluster name from clusters.yaml.")
@click.option(
    "--resource-type",
    "-t",
    multiple=True,
    type=click.Choice(RESOURCE_TYPE_CHOICES),
    help="Filter by resource type (repeatable).",
)
@click.option(
    "--resource",
    "-r",
    multiple=True,
    help="Filter by specific resource name (repeatable).",
)
@click.option(
    "--output-format",
    "-o",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format for the plan.",
)
@click.pass_context
def plan(
    ctx: click.Context,
    cluster: str,
    resource_type: tuple[str, ...],
    resource: tuple[str, ...],
    output_format: str,
) -> None:
    """Show what changes would be made to a cluster (dry run)."""
    console = Console(no_color=ctx.obj.get("no_color", False))

    try:
        config = load_config(ctx.obj["config_path"])
        if cluster not in config.clusters:
            available = ", ".join(sorted(config.clusters.keys()))
            raise ElasticodeError(
                f"Cluster '{cluster}' not found in config. Available: {available}"
            )

        client = create_client(config.clusters[cluster])

        rtypes = [RESOURCE_TYPE_MAP[rt] for rt in resource_type] if resource_type else None
        rnames = list(resource) if resource else None

        result = generate_plan(config, client, cluster, rtypes, rnames)

        if output_format == "json":
            display_plan_json(result, console)
        else:
            display_plan(result, console)

        if result.has_changes:
            raise SystemExit(2)

    except ElasticodeError as e:
        console.print(f"[red]Error:[/red] {e.message}")
        raise SystemExit(1) from None


@main.command()
@click.option("--cluster", required=True, help="Target cluster name from clusters.yaml.")
@click.option(
    "--resource-type",
    "-t",
    multiple=True,
    type=click.Choice(RESOURCE_TYPE_CHOICES),
    help="Filter by resource type (repeatable).",
)
@click.option(
    "--resource",
    "-r",
    multiple=True,
    help="Filter by specific resource name (repeatable).",
)
@click.option(
    "--auto-approve",
    "-y",
    is_flag=True,
    help="Skip confirmation prompt.",
)
@click.pass_context
def apply(
    ctx: click.Context,
    cluster: str,
    resource_type: tuple[str, ...],
    resource: tuple[str, ...],
    auto_approve: bool,
) -> None:
    """Apply changes to a cluster."""
    console = Console(no_color=ctx.obj.get("no_color", False))

    try:
        config = load_config(ctx.obj["config_path"])
        if cluster not in config.clusters:
            available = ", ".join(sorted(config.clusters.keys()))
            raise ElasticodeError(
                f"Cluster '{cluster}' not found in config. Available: {available}"
            )

        client = create_client(config.clusters[cluster])

        rtypes = [RESOURCE_TYPE_MAP[rt] for rt in resource_type] if resource_type else None
        rnames = list(resource) if resource else None

        result = generate_plan(config, client, cluster, rtypes, rnames)

        if not result.has_changes:
            console.print("[green]No changes to apply.[/green]")
            return

        # Show the plan first
        display_plan(result, console)

        # Confirm unless auto-approved
        if not auto_approve and not click.confirm("Do you want to apply these changes?"):
            console.print("[yellow]Aborted.[/yellow]")
            raise SystemExit(0)

        console.print(f"\n[bold]Applying changes to {cluster}...[/bold]\n")
        success = apply_plan(result, client, console)

        if success:
            console.print(f"\n[green]All changes applied to {cluster}.[/green]")
        else:
            console.print(f"\n[red]Some changes failed on {cluster}.[/red]")
            raise SystemExit(1)

    except ElasticodeError as e:
        console.print(f"[red]Error:[/red] {e.message}")
        raise SystemExit(1) from None
