"""Tests for terminal output formatting."""

from io import StringIO

from rich.console import Console

from elasticode.output import display_plan, display_plan_json
from elasticode.types import Plan, PlanItem, ResourceAction, ResourceType


def _make_console() -> tuple[Console, StringIO]:
    buffer = StringIO()
    console = Console(file=buffer, no_color=True, width=120)
    return console, buffer


class TestDisplayPlan:
    def test_no_changes_shows_panel(self) -> None:
        console, buffer = _make_console()
        plan = Plan(cluster_name="local", items=[])
        display_plan(plan, console)
        output = buffer.getvalue()
        assert "No changes" in output
        assert "local" in output

    def test_creates_shown(self) -> None:
        console, buffer = _make_console()
        plan = Plan(
            cluster_name="staging",
            items=[
                PlanItem(
                    resource_name="logs",
                    resource_type=ResourceType.INDEX_TEMPLATE,
                    action=ResourceAction.CREATE,
                    desired_body={"index_patterns": ["logs-*"]},
                    diff_details="+ logs-*",
                )
            ],
        )
        display_plan(plan, console)
        output = buffer.getvalue()
        assert "staging" in output
        assert "Create" in output
        assert "1 to create" in output
        assert "index_templates/logs" in output

    def test_updates_shown(self) -> None:
        console, buffer = _make_console()
        plan = Plan(
            cluster_name="prod",
            items=[
                PlanItem(
                    resource_name="logs-policy",
                    resource_type=ResourceType.ILM_POLICY,
                    action=ResourceAction.UPDATE,
                    desired_body={"policy": {}},
                    diff_details="  ~ root['policy']: changed",
                )
            ],
        )
        display_plan(plan, console)
        output = buffer.getvalue()
        assert "1 to update" in output
        assert "ilm_policies/logs-policy" in output

    def test_summary_counts(self) -> None:
        console, buffer = _make_console()
        plan = Plan(
            cluster_name="local",
            items=[
                PlanItem(
                    resource_name="a",
                    resource_type=ResourceType.INDEX_TEMPLATE,
                    action=ResourceAction.CREATE,
                    desired_body={},
                    diff_details="+ ...",
                ),
                PlanItem(
                    resource_name="b",
                    resource_type=ResourceType.ILM_POLICY,
                    action=ResourceAction.UPDATE,
                    desired_body={},
                    diff_details="~ ...",
                ),
                PlanItem(
                    resource_name="c",
                    resource_type=ResourceType.INGEST_PIPELINE,
                    action=ResourceAction.NO_CHANGE,
                    desired_body=None,
                    diff_details="",
                ),
            ],
        )
        display_plan(plan, console)
        output = buffer.getvalue()
        assert "1 to create" in output
        assert "1 to update" in output
        assert "1 unchanged" in output


class TestDisplayPlanJson:
    def test_json_output_structure(self) -> None:
        console, buffer = _make_console()
        plan = Plan(
            cluster_name="local",
            items=[
                PlanItem(
                    resource_name="logs",
                    resource_type=ResourceType.INDEX_TEMPLATE,
                    action=ResourceAction.CREATE,
                    desired_body={},
                    diff_details="",
                ),
            ],
        )
        display_plan_json(plan, console)
        output = buffer.getvalue()
        assert '"cluster": "local"' in output
        assert '"creates": 1' in output
        assert '"action": "create"' in output

    def test_json_excludes_unchanged(self) -> None:
        console, buffer = _make_console()
        plan = Plan(
            cluster_name="local",
            items=[
                PlanItem(
                    resource_name="a",
                    resource_type=ResourceType.INDEX_TEMPLATE,
                    action=ResourceAction.NO_CHANGE,
                    desired_body=None,
                    diff_details="",
                ),
            ],
        )
        display_plan_json(plan, console)
        output = buffer.getvalue()
        assert '"items": []' in output
