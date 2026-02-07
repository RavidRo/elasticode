"""Shared data types for Elasticode."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class ResourceType(Enum):
    """Supported Elasticsearch resource types."""

    INDEX_TEMPLATE = "index_templates"
    COMPONENT_TEMPLATE = "component_templates"
    ILM_POLICY = "ilm_policies"
    INGEST_PIPELINE = "ingest_pipelines"


class ResourceAction(Enum):
    """Actions that can be taken on a resource."""

    CREATE = "create"
    UPDATE = "update"
    NO_CHANGE = "no_change"


@dataclass(frozen=True)
class TlsConfig:
    """TLS configuration for an Elasticsearch cluster."""

    verify: bool = True
    ca_cert: str | None = None


@dataclass(frozen=True)
class AuthConfig:
    """Authentication configuration for an Elasticsearch cluster."""

    type: str  # "basic" | "api_key" | "bearer"
    username: str | None = None
    password: str | None = None
    api_key: str | None = None
    token: str | None = None


@dataclass(frozen=True)
class ClusterConfig:
    """Configuration for a single Elasticsearch cluster."""

    url: str
    auth: AuthConfig
    tls: TlsConfig


@dataclass(frozen=True)
class ElasticodeConfig:
    """Top-level Elasticode configuration."""

    clusters: dict[str, ClusterConfig]
    resource_dir: Path


@dataclass(frozen=True)
class DesiredResource:
    """A resource loaded from a local JSON file."""

    name: str
    resource_type: ResourceType
    body: dict[str, Any]
    file_path: Path


@dataclass(frozen=True)
class DiffResult:
    """The result of comparing desired vs current state for one resource."""

    resource_name: str
    resource_type: ResourceType
    action: ResourceAction
    desired: dict[str, Any] | None
    current: dict[str, Any] | None
    diff_details: str


@dataclass(frozen=True)
class PlanItem:
    """A single action in a plan."""

    resource_name: str
    resource_type: ResourceType
    action: ResourceAction
    desired_body: dict[str, Any] | None
    diff_details: str


@dataclass(frozen=True)
class Plan:
    """A complete plan of changes to apply."""

    cluster_name: str
    items: list[PlanItem] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return any(item.action != ResourceAction.NO_CHANGE for item in self.items)

    @property
    def creates(self) -> list[PlanItem]:
        return [i for i in self.items if i.action == ResourceAction.CREATE]

    @property
    def updates(self) -> list[PlanItem]:
        return [i for i in self.items if i.action == ResourceAction.UPDATE]

    @property
    def unchanged(self) -> list[PlanItem]:
        return [i for i in self.items if i.action == ResourceAction.NO_CHANGE]


@dataclass(frozen=True)
class ExportResult:
    """Result of an export operation."""

    cluster_name: str
    exported: list[tuple[ResourceType, str]] = field(default_factory=list)
    skipped: list[tuple[ResourceType, str, str]] = field(default_factory=list)

    @property
    def exported_count(self) -> int:
        return len(self.exported)

    @property
    def skipped_count(self) -> int:
        return len(self.skipped)
