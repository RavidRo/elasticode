"""Export resources from an Elasticsearch cluster to local JSON files."""

import json
from pathlib import Path
from typing import Any

from elasticsearch import Elasticsearch

from elasticode.errors import ExportError
from elasticode.resources import get_handler
from elasticode.types import ExportResult, ResourceType


def export_resources(
    client: Elasticsearch,
    cluster_name: str,
    output_dir: Path,
    resource_types: list[ResourceType] | None = None,
    resource_names: list[str] | None = None,
    force: bool = False,
) -> ExportResult:
    """Export resources from an ES cluster to local JSON files."""
    types_to_export = resource_types or list(ResourceType)
    exported: list[tuple[ResourceType, str]] = []
    skipped: list[tuple[ResourceType, str, str]] = []

    for rtype in types_to_export:
        handler = get_handler(rtype, client)
        try:
            all_resources = handler.list_all()
        except Exception as e:
            raise ExportError(
                f"Failed to list {rtype.value} from cluster '{cluster_name}': {e}"
            ) from e

        for name, body in sorted(all_resources.items()):
            if resource_names and name not in resource_names:
                continue

            dir_path = output_dir / rtype.value
            dir_path.mkdir(parents=True, exist_ok=True)
            file_path = dir_path / f"{name}.json"

            if file_path.exists() and not force:
                skipped.append((rtype, name, "file already exists"))
                continue

            _write_resource_file(file_path, body)
            exported.append((rtype, name))

    return ExportResult(
        cluster_name=cluster_name,
        exported=exported,
        skipped=skipped,
    )


def _write_resource_file(path: Path, body: dict[str, Any]) -> None:
    """Write a resource body as formatted JSON."""
    with path.open("w") as f:
        json.dump(body, f, indent=2)
        f.write("\n")
