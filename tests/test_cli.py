"""Tests for the CLI interface."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from elasticode.cli import main
from elasticode.types import (
    ExportResult,
    Plan,
    PlanItem,
    ResourceAction,
    ResourceType,
)


class TestCliInit:
    def test_init_creates_project(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        result = cli_runner.invoke(main, ["init", "--directory", str(tmp_path)])
        assert result.exit_code == 0
        assert "Project initialized" in result.output
        assert (tmp_path / "clusters.yaml").exists()
        assert (tmp_path / "index_templates").is_dir()

    def test_init_shows_next_steps(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        result = cli_runner.invoke(main, ["init", "--directory", str(tmp_path)])
        assert "Next steps" in result.output
        assert "elasticode validate" in result.output
        assert "elasticode plan" in result.output

    def test_init_existing_project(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        # First init
        cli_runner.invoke(main, ["init", "--directory", str(tmp_path)])
        # Second init should note existing project
        result = cli_runner.invoke(main, ["init", "--directory", str(tmp_path)])
        assert result.exit_code == 0


class TestCliValidate:
    def test_validate_valid_files(self, cli_runner: CliRunner, fixtures_dir: Path) -> None:
        result = cli_runner.invoke(
            main, ["--config", str(fixtures_dir / "clusters.yaml"), "validate"]
        )
        assert result.exit_code == 0
        assert "OK" in result.output
        assert "valid" in result.output.lower()

    def test_validate_missing_config(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(main, ["--config", "/nonexistent/clusters.yaml", "validate"])
        assert result.exit_code == 1
        assert "Error" in result.output

    def test_validate_with_type_filter(self, cli_runner: CliRunner, fixtures_dir: Path) -> None:
        result = cli_runner.invoke(
            main,
            [
                "--config",
                str(fixtures_dir / "clusters.yaml"),
                "validate",
                "-t",
                "index_templates",
            ],
        )
        assert result.exit_code == 0
        assert "index_templates" in result.output


class TestCliPlan:
    def test_plan_unknown_cluster(self, cli_runner: CliRunner, fixtures_dir: Path) -> None:
        result = cli_runner.invoke(
            main,
            [
                "--config",
                str(fixtures_dir / "clusters.yaml"),
                "plan",
                "--cluster",
                "nonexistent",
            ],
        )
        assert result.exit_code == 1
        assert "nonexistent" in result.output
        assert "Available" in result.output

    @patch("elasticode.cli.create_client")
    @patch("elasticode.cli.generate_plan")
    def test_plan_no_changes(
        self,
        mock_generate: MagicMock,
        mock_client: MagicMock,
        cli_runner: CliRunner,
        fixtures_dir: Path,
    ) -> None:
        mock_generate.return_value = Plan(cluster_name="local", items=[])
        result = cli_runner.invoke(
            main,
            [
                "--config",
                str(fixtures_dir / "clusters.yaml"),
                "plan",
                "--cluster",
                "local",
            ],
        )
        assert result.exit_code == 0
        assert "No changes" in result.output

    @patch("elasticode.cli.create_client")
    @patch("elasticode.cli.generate_plan")
    def test_plan_with_changes_exits_2(
        self,
        mock_generate: MagicMock,
        mock_client: MagicMock,
        cli_runner: CliRunner,
        fixtures_dir: Path,
    ) -> None:
        mock_generate.return_value = Plan(
            cluster_name="local",
            items=[
                PlanItem(
                    resource_name="logs",
                    resource_type=ResourceType.INDEX_TEMPLATE,
                    action=ResourceAction.CREATE,
                    desired_body={"index_patterns": ["logs-*"]},
                    diff_details="+ ...",
                )
            ],
        )
        result = cli_runner.invoke(
            main,
            [
                "--config",
                str(fixtures_dir / "clusters.yaml"),
                "plan",
                "--cluster",
                "local",
            ],
        )
        assert result.exit_code == 2

    @patch("elasticode.cli.create_client")
    @patch("elasticode.cli.generate_plan")
    def test_plan_json_output(
        self,
        mock_generate: MagicMock,
        mock_client: MagicMock,
        cli_runner: CliRunner,
        fixtures_dir: Path,
    ) -> None:
        mock_generate.return_value = Plan(
            cluster_name="local",
            items=[
                PlanItem(
                    resource_name="logs",
                    resource_type=ResourceType.INDEX_TEMPLATE,
                    action=ResourceAction.CREATE,
                    desired_body={},
                    diff_details="",
                )
            ],
        )
        result = cli_runner.invoke(
            main,
            [
                "--config",
                str(fixtures_dir / "clusters.yaml"),
                "plan",
                "--cluster",
                "local",
                "-o",
                "json",
            ],
        )
        assert '"cluster": "local"' in result.output


class TestCliApply:
    @patch("elasticode.cli.create_client")
    @patch("elasticode.cli.generate_plan")
    def test_apply_no_changes(
        self,
        mock_generate: MagicMock,
        mock_client: MagicMock,
        cli_runner: CliRunner,
        fixtures_dir: Path,
    ) -> None:
        mock_generate.return_value = Plan(cluster_name="local", items=[])
        result = cli_runner.invoke(
            main,
            [
                "--config",
                str(fixtures_dir / "clusters.yaml"),
                "apply",
                "--cluster",
                "local",
            ],
        )
        assert result.exit_code == 0
        assert "No changes" in result.output

    @patch("elasticode.cli.apply_plan")
    @patch("elasticode.cli.create_client")
    @patch("elasticode.cli.generate_plan")
    def test_apply_with_auto_approve(
        self,
        mock_generate: MagicMock,
        mock_client: MagicMock,
        mock_apply: MagicMock,
        cli_runner: CliRunner,
        fixtures_dir: Path,
    ) -> None:
        mock_generate.return_value = Plan(
            cluster_name="local",
            items=[
                PlanItem(
                    resource_name="logs",
                    resource_type=ResourceType.INDEX_TEMPLATE,
                    action=ResourceAction.CREATE,
                    desired_body={"index_patterns": ["logs-*"]},
                    diff_details="+ ...",
                )
            ],
        )
        mock_apply.return_value = True
        result = cli_runner.invoke(
            main,
            [
                "--config",
                str(fixtures_dir / "clusters.yaml"),
                "apply",
                "--cluster",
                "local",
                "--auto-approve",
            ],
        )
        assert result.exit_code == 0
        assert "applied" in result.output.lower()
        mock_apply.assert_called_once()

    @patch("elasticode.cli.create_client")
    @patch("elasticode.cli.generate_plan")
    def test_apply_aborted_by_user(
        self,
        mock_generate: MagicMock,
        mock_client: MagicMock,
        cli_runner: CliRunner,
        fixtures_dir: Path,
    ) -> None:
        mock_generate.return_value = Plan(
            cluster_name="local",
            items=[
                PlanItem(
                    resource_name="logs",
                    resource_type=ResourceType.INDEX_TEMPLATE,
                    action=ResourceAction.CREATE,
                    desired_body={},
                    diff_details="+ ...",
                )
            ],
        )
        result = cli_runner.invoke(
            main,
            [
                "--config",
                str(fixtures_dir / "clusters.yaml"),
                "apply",
                "--cluster",
                "local",
            ],
            input="n\n",
        )
        assert "Aborted" in result.output

    def test_apply_unknown_cluster(self, cli_runner: CliRunner, fixtures_dir: Path) -> None:
        result = cli_runner.invoke(
            main,
            [
                "--config",
                str(fixtures_dir / "clusters.yaml"),
                "apply",
                "--cluster",
                "nonexistent",
            ],
        )
        assert result.exit_code == 1
        assert "nonexistent" in result.output


class TestCliExport:
    def test_export_unknown_cluster(self, cli_runner: CliRunner, fixtures_dir: Path) -> None:
        result = cli_runner.invoke(
            main,
            [
                "--config",
                str(fixtures_dir / "clusters.yaml"),
                "export",
                "--cluster",
                "nonexistent",
            ],
        )
        assert result.exit_code == 1
        assert "nonexistent" in result.output
        assert "Available" in result.output

    @patch("elasticode.cli.create_client")
    @patch("elasticode.cli.export_resources")
    def test_export_success(
        self,
        mock_export: MagicMock,
        mock_client: MagicMock,
        cli_runner: CliRunner,
        fixtures_dir: Path,
    ) -> None:
        mock_export.return_value = ExportResult(
            cluster_name="local",
            exported=[(ResourceType.INDEX_TEMPLATE, "logs")],
            skipped=[],
        )
        result = cli_runner.invoke(
            main,
            [
                "--config",
                str(fixtures_dir / "clusters.yaml"),
                "export",
                "--cluster",
                "local",
            ],
        )
        assert result.exit_code == 0
        assert "Exported 1" in result.output
        assert "OK" in result.output

    @patch("elasticode.cli.create_client")
    @patch("elasticode.cli.export_resources")
    def test_export_with_skips(
        self,
        mock_export: MagicMock,
        mock_client: MagicMock,
        cli_runner: CliRunner,
        fixtures_dir: Path,
    ) -> None:
        mock_export.return_value = ExportResult(
            cluster_name="local",
            exported=[],
            skipped=[(ResourceType.INDEX_TEMPLATE, "logs", "file already exists")],
        )
        result = cli_runner.invoke(
            main,
            [
                "--config",
                str(fixtures_dir / "clusters.yaml"),
                "export",
                "--cluster",
                "local",
            ],
        )
        assert result.exit_code == 0
        assert "SKIP" in result.output
        assert "file already exists" in result.output
        assert "--force" in result.output

    def test_export_missing_config(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(
            main,
            ["--config", "/nonexistent/clusters.yaml", "export", "--cluster", "local"],
        )
        assert result.exit_code == 1
        assert "Error" in result.output


class TestCliVersion:
    def test_version_flag(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output
