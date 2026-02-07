"""Resource file discovery and JSON loading."""

import json
from pathlib import Path
from typing import Any

from elasticode.errors import ValidationError
from elasticode.types import DesiredResource, ResourceType


def discover_resources(
    base_dir: Path,
    resource_types: list[ResourceType] | None = None,
    resource_names: list[str] | None = None,
) -> list[DesiredResource]:
    """Discover and load all JSON resource files from the resource directories.

    Args:
        base_dir: Root directory containing resource type subdirectories.
        resource_types: If given, only load these resource types.
        resource_names: If given, only load resources with these names.

    Returns:
        List of DesiredResource objects sorted by type then name.
    """
    resources: list[DesiredResource] = []
    types_to_scan = resource_types or list(ResourceType)

    for rtype in types_to_scan:
        dir_path = base_dir / rtype.value
        if not dir_path.is_dir():
            continue

        for json_file in sorted(dir_path.glob("*.json")):
            resource_name = json_file.stem
            if resource_names and resource_name not in resource_names:
                continue

            body = _load_json_file(json_file)
            resources.append(
                DesiredResource(
                    name=resource_name,
                    resource_type=rtype,
                    body=body,
                    file_path=json_file,
                )
            )

    return resources


def validate_resources(
    base_dir: Path,
    resource_types: list[ResourceType] | None = None,
    resource_names: list[str] | None = None,
) -> list[str]:
    """Validate all resource files and return a list of error messages.

    Returns an empty list if all files are valid.
    """
    errors: list[str] = []
    types_to_scan = resource_types or list(ResourceType)

    for rtype in types_to_scan:
        dir_path = base_dir / rtype.value
        if not dir_path.is_dir():
            continue

        for json_file in sorted(dir_path.glob("*.json")):
            resource_name = json_file.stem
            if resource_names and resource_name not in resource_names:
                continue

            try:
                _load_json_file(json_file)
            except ValidationError as e:
                errors.append(e.message)

    return errors


def _load_json_file(path: Path) -> dict[str, Any]:
    """Load and parse a JSON file, with clear error messages."""
    try:
        with path.open() as f:
            data: Any = json.load(f)
    except json.JSONDecodeError as e:
        raise ValidationError(
            f"Invalid JSON in {path}: {e.msg} (line {e.lineno}, col {e.colno})"
        ) from e
    except OSError as e:
        raise ValidationError(f"Cannot read file {path}: {e}") from e

    if not isinstance(data, dict):
        raise ValidationError(
            f"Resource file {path} must contain a JSON object, got {type(data).__name__}."
        )

    return data
