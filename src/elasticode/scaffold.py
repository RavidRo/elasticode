"""Project scaffolding for the `init` command."""

from pathlib import Path

from elasticode.types import ResourceType

EXAMPLE_CLUSTER_CONFIG = """\
# Elasticode cluster configuration
# Docs: https://github.com/ravidrom/elasticode#configuration
clusters:
  local:
    url: "http://localhost:9200"
    auth:
      type: "basic"
      username: "elastic"
      password: "${ES_PASSWORD}"
    tls:
      verify: false

  # Example remote cluster (uncomment and configure):
  # production:
  #   url: "https://es-prod.example.com:9200"
  #   auth:
  #     type: "api_key"
  #     api_key: "${ES_PROD_API_KEY}"
  #   tls:
  #     verify: true
  #     ca_cert: "/path/to/ca.pem"
"""

EXAMPLE_INDEX_TEMPLATE = """\
{
  "index_patterns": ["logs-*"],
  "priority": 100,
  "template": {
    "settings": {
      "number_of_shards": 1,
      "number_of_replicas": 1
    },
    "mappings": {
      "properties": {
        "@timestamp": { "type": "date" },
        "message": { "type": "text" }
      }
    }
  }
}
"""

GITIGNORE_CONTENT = """\
# Elasticode
# Never commit secrets - use ${ENV_VAR} references in clusters.yaml
*.env
.env*
"""


def scaffold_project(directory: Path) -> list[Path]:
    """Create starter project structure. Returns list of created paths."""
    created: list[Path] = []

    # Create resource directories
    for rtype in ResourceType:
        dir_path = directory / rtype.value
        dir_path.mkdir(parents=True, exist_ok=True)
        created.append(dir_path)

    # Create clusters.yaml
    config_path = directory / "clusters.yaml"
    if not config_path.exists():
        config_path.write_text(EXAMPLE_CLUSTER_CONFIG)
        created.append(config_path)

    # Create example index template
    example_path = directory / "index_templates" / "example-logs.json"
    if not example_path.exists():
        example_path.write_text(EXAMPLE_INDEX_TEMPLATE)
        created.append(example_path)

    # Create .gitignore
    gitignore_path = directory / ".gitignore"
    if not gitignore_path.exists():
        gitignore_path.write_text(GITIGNORE_CONTENT)
        created.append(gitignore_path)

    return created
