"""Tests for resource file discovery and loading."""

from pathlib import Path

import pytest

from elasticode.errors import ValidationError
from elasticode.loader import discover_resources, validate_resources
from elasticode.types import ResourceType


class TestDiscoverResources:
    def test_discovers_all_resource_types(self, fixtures_dir: Path) -> None:
        resources = discover_resources(fixtures_dir)
        types_found = {r.resource_type for r in resources}
        assert ResourceType.INDEX_TEMPLATE in types_found
        assert ResourceType.COMPONENT_TEMPLATE in types_found
        assert ResourceType.ILM_POLICY in types_found
        assert ResourceType.INGEST_PIPELINE in types_found

    def test_resource_names_from_filenames(self, fixtures_dir: Path) -> None:
        resources = discover_resources(fixtures_dir)
        names = {r.name for r in resources}
        assert "logs-template" in names
        assert "base-mappings" in names
        assert "logs-policy" in names
        assert "parse-logs" in names

    def test_filter_by_resource_type(self, fixtures_dir: Path) -> None:
        resources = discover_resources(fixtures_dir, resource_types=[ResourceType.INDEX_TEMPLATE])
        assert all(r.resource_type == ResourceType.INDEX_TEMPLATE for r in resources)
        assert len(resources) == 1

    def test_filter_by_resource_name(self, fixtures_dir: Path) -> None:
        resources = discover_resources(fixtures_dir, resource_names=["logs-template"])
        assert len(resources) == 1
        assert resources[0].name == "logs-template"

    def test_missing_directory_is_skipped(self, tmp_path: Path) -> None:
        resources = discover_resources(tmp_path)
        assert resources == []

    def test_resource_body_is_dict(self, fixtures_dir: Path) -> None:
        resources = discover_resources(fixtures_dir)
        for r in resources:
            assert isinstance(r.body, dict)

    def test_file_path_is_set(self, fixtures_dir: Path) -> None:
        resources = discover_resources(fixtures_dir)
        for r in resources:
            assert r.file_path.exists()
            assert r.file_path.suffix == ".json"

    def test_invalid_json_raises(self, tmp_path: Path) -> None:
        index_dir = tmp_path / "index_templates"
        index_dir.mkdir()
        bad_file = index_dir / "bad.json"
        bad_file.write_text("{invalid json")
        with pytest.raises(ValidationError, match="Invalid JSON"):
            discover_resources(tmp_path)

    def test_non_object_json_raises(self, tmp_path: Path) -> None:
        index_dir = tmp_path / "index_templates"
        index_dir.mkdir()
        bad_file = index_dir / "array.json"
        bad_file.write_text("[1, 2, 3]")
        with pytest.raises(ValidationError, match="must contain a JSON object"):
            discover_resources(tmp_path)

    def test_combined_type_and_name_filter(self, fixtures_dir: Path) -> None:
        resources = discover_resources(
            fixtures_dir,
            resource_types=[ResourceType.ILM_POLICY],
            resource_names=["logs-policy"],
        )
        assert len(resources) == 1
        assert resources[0].name == "logs-policy"
        assert resources[0].resource_type == ResourceType.ILM_POLICY


class TestValidateResources:
    def test_valid_resources_return_empty(self, fixtures_dir: Path) -> None:
        errors = validate_resources(fixtures_dir)
        assert errors == []

    def test_invalid_json_returns_errors(self, tmp_path: Path) -> None:
        index_dir = tmp_path / "index_templates"
        index_dir.mkdir()
        bad_file = index_dir / "bad.json"
        bad_file.write_text("{not json}")
        errors = validate_resources(tmp_path)
        assert len(errors) == 1
        assert "Invalid JSON" in errors[0]

    def test_multiple_errors_reported(self, tmp_path: Path) -> None:
        index_dir = tmp_path / "index_templates"
        index_dir.mkdir()
        (index_dir / "bad1.json").write_text("{not json}")
        (index_dir / "bad2.json").write_text("[1,2]")
        errors = validate_resources(tmp_path)
        assert len(errors) == 2
