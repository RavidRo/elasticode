"""Tests for project scaffolding."""

from pathlib import Path

from elasticode.scaffold import scaffold_project
from elasticode.types import ResourceType


class TestScaffoldProject:
    def test_creates_all_resource_directories(self, tmp_path: Path) -> None:
        scaffold_project(tmp_path)
        for rtype in ResourceType:
            assert (tmp_path / rtype.value).is_dir()

    def test_creates_clusters_yaml(self, tmp_path: Path) -> None:
        scaffold_project(tmp_path)
        config_path = tmp_path / "clusters.yaml"
        assert config_path.exists()
        content = config_path.read_text()
        assert "clusters:" in content
        assert "local:" in content

    def test_creates_example_template(self, tmp_path: Path) -> None:
        scaffold_project(tmp_path)
        example = tmp_path / "index_templates" / "example-logs.json"
        assert example.exists()
        content = example.read_text()
        assert "index_patterns" in content

    def test_creates_gitignore(self, tmp_path: Path) -> None:
        scaffold_project(tmp_path)
        gitignore = tmp_path / ".gitignore"
        assert gitignore.exists()
        content = gitignore.read_text()
        assert ".env" in content

    def test_returns_created_paths(self, tmp_path: Path) -> None:
        created = scaffold_project(tmp_path)
        assert len(created) > 0
        # Should have 5 dirs + clusters.yaml + example + .gitignore = 8
        assert len(created) == 8

    def test_does_not_overwrite_existing_files(self, tmp_path: Path) -> None:
        # First scaffold
        scaffold_project(tmp_path)
        # Modify clusters.yaml
        config_path = tmp_path / "clusters.yaml"
        config_path.write_text("custom content")

        # Second scaffold should not overwrite
        created = scaffold_project(tmp_path)
        assert config_path.read_text() == "custom content"
        # Only dirs should be "created" (they exist but mkdir is ok)
        assert config_path not in created

    def test_scaffold_in_nested_directory(self, tmp_path: Path) -> None:
        nested = tmp_path / "my" / "project"
        scaffold_project(nested)
        assert (nested / "clusters.yaml").exists()
        assert (nested / "index_templates").is_dir()
