"""Tests for plan execution."""

from unittest.mock import MagicMock

from rich.console import Console

from elasticode.applier import apply_plan
from elasticode.types import Plan, PlanItem, ResourceAction, ResourceType


class TestApplyPlan:
    def test_apply_empty_plan(self, mock_es_client: MagicMock) -> None:
        console = Console(file=MagicMock(), no_color=True)
        plan = Plan(cluster_name="local", items=[])
        result = apply_plan(plan, mock_es_client, console)
        assert result is True

    def test_apply_plan_with_no_changes(self, mock_es_client: MagicMock) -> None:
        console = Console(file=MagicMock(), no_color=True)
        plan = Plan(
            cluster_name="local",
            items=[
                PlanItem(
                    resource_name="logs",
                    resource_type=ResourceType.INDEX_TEMPLATE,
                    action=ResourceAction.NO_CHANGE,
                    desired_body=None,
                    diff_details="",
                )
            ],
        )
        result = apply_plan(plan, mock_es_client, console)
        assert result is True

    def test_apply_create(self, mock_es_client: MagicMock) -> None:
        console = Console(file=MagicMock(), no_color=True)
        body = {"index_patterns": ["logs-*"]}
        plan = Plan(
            cluster_name="local",
            items=[
                PlanItem(
                    resource_name="logs",
                    resource_type=ResourceType.INDEX_TEMPLATE,
                    action=ResourceAction.CREATE,
                    desired_body=body,
                    diff_details="+ ...",
                )
            ],
        )
        result = apply_plan(plan, mock_es_client, console)
        assert result is True
        mock_es_client.indices.put_index_template.assert_called_once_with(name="logs", **body)

    def test_apply_update(self, mock_es_client: MagicMock) -> None:
        console = Console(file=MagicMock(), no_color=True)
        body = {"index_patterns": ["logs-*"], "priority": 200}
        plan = Plan(
            cluster_name="local",
            items=[
                PlanItem(
                    resource_name="logs",
                    resource_type=ResourceType.INDEX_TEMPLATE,
                    action=ResourceAction.UPDATE,
                    desired_body=body,
                    diff_details="~ ...",
                )
            ],
        )
        result = apply_plan(plan, mock_es_client, console)
        assert result is True
        mock_es_client.indices.put_index_template.assert_called_once_with(name="logs", **body)

    def test_apply_handles_failure(self, mock_es_client: MagicMock) -> None:
        console = Console(file=MagicMock(), no_color=True)
        mock_es_client.indices.put_index_template.side_effect = Exception("Connection refused")
        body = {"index_patterns": ["logs-*"]}
        plan = Plan(
            cluster_name="local",
            items=[
                PlanItem(
                    resource_name="logs",
                    resource_type=ResourceType.INDEX_TEMPLATE,
                    action=ResourceAction.CREATE,
                    desired_body=body,
                    diff_details="+ ...",
                )
            ],
        )
        result = apply_plan(plan, mock_es_client, console)
        assert result is False

    def test_apply_multiple_items(self, mock_es_client: MagicMock) -> None:
        console = Console(file=MagicMock(), no_color=True)
        plan = Plan(
            cluster_name="local",
            items=[
                PlanItem(
                    resource_name="logs",
                    resource_type=ResourceType.INDEX_TEMPLATE,
                    action=ResourceAction.CREATE,
                    desired_body={"index_patterns": ["logs-*"]},
                    diff_details="+ ...",
                ),
                PlanItem(
                    resource_name="parse-logs",
                    resource_type=ResourceType.INGEST_PIPELINE,
                    action=ResourceAction.UPDATE,
                    desired_body={"description": "Parse logs", "processors": []},
                    diff_details="~ ...",
                ),
                PlanItem(
                    resource_name="unchanged",
                    resource_type=ResourceType.ILM_POLICY,
                    action=ResourceAction.NO_CHANGE,
                    desired_body=None,
                    diff_details="",
                ),
            ],
        )
        result = apply_plan(plan, mock_es_client, console)
        assert result is True
        # Only 2 put calls (NO_CHANGE should be skipped)
        mock_es_client.indices.put_index_template.assert_called_once()
        mock_es_client.ingest.put_pipeline.assert_called_once()
