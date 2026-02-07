"""Diff engine: compare desired vs current Elasticsearch resource state."""

import json
from typing import Any

from deepdiff import DeepDiff

from elasticode.resources.base import ResourceHandler
from elasticode.types import (
    DesiredResource,
    DiffResult,
    ResourceAction,
)


def diff_resource(
    desired: DesiredResource,
    handler: ResourceHandler,
) -> DiffResult:
    """Compare a single desired resource against its current state in ES."""
    current = handler.get(desired.name)

    if current is None:
        return DiffResult(
            resource_name=desired.name,
            resource_type=desired.resource_type,
            action=ResourceAction.CREATE,
            desired=desired.body,
            current=None,
            diff_details=_format_create_diff(desired.body),
        )

    normalized_desired = handler.normalize(desired.body)
    normalized_current = handler.normalize(current)

    deep_diff = DeepDiff(
        normalized_current,
        normalized_desired,
        ignore_order=True,
        verbose_level=2,
    )

    if not deep_diff:
        return DiffResult(
            resource_name=desired.name,
            resource_type=desired.resource_type,
            action=ResourceAction.NO_CHANGE,
            desired=desired.body,
            current=current,
            diff_details="",
        )

    return DiffResult(
        resource_name=desired.name,
        resource_type=desired.resource_type,
        action=ResourceAction.UPDATE,
        desired=desired.body,
        current=current,
        diff_details=_format_update_diff(deep_diff),
    )


def _format_create_diff(body: dict[str, Any]) -> str:
    """Format diff for a new resource (all additions)."""
    lines = json.dumps(body, indent=2).splitlines()
    return "\n".join(f"+ {line}" for line in lines)


def _format_update_diff(deep_diff: DeepDiff) -> str:
    """Format diff for an updated resource showing what changed."""
    lines: list[str] = []

    changed: dict[str, Any] = deep_diff.get("values_changed", {})
    for path, change in changed.items():
        lines.append(f"  ~ {path}:")
        lines.append(f"    - {json.dumps(change['old_value'])}")
        lines.append(f"    + {json.dumps(change['new_value'])}")

    added: dict[str, Any] = deep_diff.get("dictionary_item_added", {})
    for path, value in added.items():
        lines.append(f"  + {path}: {json.dumps(value)}")

    removed: dict[str, Any] = deep_diff.get("dictionary_item_removed", {})
    for path, value in removed.items():
        lines.append(f"  - {path}: {json.dumps(value)}")

    iter_added: dict[str, Any] = deep_diff.get("iterable_item_added", {})
    for path, value in iter_added.items():
        lines.append(f"  + {path}: {json.dumps(value)}")

    iter_removed: dict[str, Any] = deep_diff.get("iterable_item_removed", {})
    for path, value in iter_removed.items():
        lines.append(f"  - {path}: {json.dumps(value)}")

    type_changes: dict[str, Any] = deep_diff.get("type_changes", {})
    for path, change in type_changes.items():
        lines.append(f"  ~ {path}:")
        lines.append(f"    - {json.dumps(change['old_value'])}")
        lines.append(f"    + {json.dumps(change['new_value'])}")

    return "\n".join(lines)
