# Elasticode

Declaratively manage Elasticsearch 8.x resources with a Terraform-like workflow.

Define your Elasticsearch resources as JSON files, organize them by type, and use `elasticode plan` / `elasticode apply` to preview and push changes to your clusters.

## Features

- **Declarative resource management** -- define index templates, component templates, ILM policies, ingest pipelines, and indices as JSON files
- **Plan/apply workflow** -- preview changes before applying them, just like Terraform
- **Export existing resources** -- fetch resources from a cluster and save them as local JSON files for easy migration
- **Multi-cluster support** -- manage multiple Elasticsearch clusters from a single config file
- **Environment variable interpolation** -- keep secrets out of config files with `${ENV_VAR}` references
- **Colored diff output** -- see exactly what will change before applying
- **JSON output** -- machine-readable plan output for CI/CD pipelines

## Installation

```bash
pip install elasticode
```

Requires Python 3.13+.

## Quick Start

### 1. Initialize a project

```bash
elasticode init
```

This creates a starter project structure:

```
.
├── clusters.yaml
├── .gitignore
├── index_templates/
│   └── example-logs.json
├── component_templates/
├── ilm_policies/
├── ingest_pipelines/
└── indices/
```

### 2. Configure your clusters

Edit `clusters.yaml` with your Elasticsearch cluster details:

```yaml
clusters:
  production:
    url: "https://es-prod.example.com:9200"
    auth:
      type: "basic"
      username: "${ES_USERNAME}"
      password: "${ES_PASSWORD}"
    tls:
      verify: true
      ca_cert: "/path/to/ca.pem"

  local:
    url: "http://localhost:9200"
    auth:
      type: "basic"
      username: "elastic"
      password: "changeme"
    tls:
      verify: false
```

### 3. Add resource files

Create JSON files in the appropriate directories. The filename (without `.json`) becomes the resource name in Elasticsearch.

**Index template** (`index_templates/logs.json`):

```json
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
```

**ILM policy** (`ilm_policies/logs-lifecycle.json`):

```json
{
  "policy": {
    "phases": {
      "hot": {
        "min_age": "0ms",
        "actions": {
          "rollover": {
            "max_primary_shard_size": "50gb",
            "max_age": "30d"
          }
        }
      },
      "delete": {
        "min_age": "90d",
        "actions": {
          "delete": {}
        }
      }
    }
  }
}
```

### 4. Validate your files

```bash
elasticode validate
```

### 5. Preview changes

```bash
elasticode plan --cluster local
```

Output:

```
Plan for cluster: local

  Change Summary
  ┌──────────┬───────┐
  │ Action   │ Count │
  ├──────────┼───────┤
  │ Create   │     2 │
  │ Update   │     0 │
  │ Unchanged│     0 │
  └──────────┴───────┘

  + index_templates/logs
      + { "index_patterns": ["logs-*"], ... }

  + ilm_policies/logs-lifecycle
      + { "policy": { "phases": { ... } } }

Total: 2 to create, 0 to update, 0 unchanged.
```

### 6. Apply changes

```bash
elasticode apply --cluster local
```

You'll be prompted to confirm before changes are applied. Use `--auto-approve` / `-y` to skip the prompt (useful in CI).

## CLI Reference

```
elasticode [OPTIONS] COMMAND [ARGS]

Options:
  -c, --config PATH   Path to clusters.yaml (default: clusters.yaml)
  -q, --quiet         Suppress non-essential output
  --no-color          Disable colored output
  --version           Show version and exit

Commands:
  init       Scaffold a new Elasticode project
  export     Export resources from a cluster to local JSON files
  validate   Validate JSON resource files and cluster config
  plan       Show what changes would be made (dry run)
  apply      Apply changes to a cluster
```

### `elasticode export`

Fetch existing resources from a cluster and write them as JSON files. Useful for migrating an existing cluster to Elasticode management.

```
Options:
  --cluster TEXT       Target cluster name (required)
  -t, --resource-type  Filter by type (repeatable)
  -r, --resource TEXT  Filter by resource name (repeatable)
  -d, --directory PATH Output directory (default: current directory)
  -f, --force          Overwrite existing files
```

Example:

```bash
# Export all resources from production cluster
elasticode export --cluster production

# Export only index templates
elasticode export --cluster production -t index_templates

# Export to a specific directory
elasticode export --cluster production -d ./backup

# Overwrite existing files
elasticode export --cluster production --force
```

### `elasticode plan`

```
Options:
  --cluster TEXT       Target cluster name (required)
  -t, --resource-type  Filter by type: index_templates, component_templates,
                        ilm_policies, ingest_pipelines (repeatable)
  -r, --resource TEXT  Filter by resource name (repeatable)
  -o, --output-format  Output format: text (default) or json
```

Exit codes:
- `0` -- no changes needed
- `1` -- error occurred
- `2` -- changes detected (useful in CI to detect drift)

### `elasticode apply`

```
Options:
  --cluster TEXT       Target cluster name (required)
  -t, --resource-type  Filter by type (repeatable)
  -r, --resource TEXT  Filter by resource name (repeatable)
  -y, --auto-approve  Skip confirmation prompt
```

## Supported Resources

| Resource | Directory | Elasticsearch API | Notes |
|---|---|---|---|
| Index templates | `index_templates/` | `_index_template` | |
| Component templates | `component_templates/` | `_component_template` | |
| ILM policies | `ilm_policies/` | `_ilm/policy` | |
| Ingest pipelines | `ingest_pipelines/` | `_ingest/pipeline` | |
| Indices | `indices/` | `/{index}` | **Create-only** for safety (updates/deletes blocked) |

### Index Safety

Indices are treated specially for safety because they contain data:

- **Creating new indices**: Allowed — define settings and mappings in JSON files
- **Updating existing indices**: Blocked — indices are largely immutable (most settings/mappings can't be changed)
- **Deleting indices**: Blocked — use the Elasticsearch API directly if you need to delete an index

This create-only mode prevents accidental data loss. If you need to modify an existing index, you should:
1. Use the Elasticsearch API to update dynamic settings that support updates
2. Or use the reindex API to create a new index with updated mappings

System indices (those starting with `.` like `.kibana`, `.security`) are automatically filtered from `export` and `list` operations.

## Configuration

### Cluster authentication

Three auth methods are supported:

**Basic auth:**

```yaml
auth:
  type: "basic"
  username: "${ES_USERNAME}"
  password: "${ES_PASSWORD}"
```

**API key:**

```yaml
auth:
  type: "api_key"
  api_key: "${ES_API_KEY}"
```

**Bearer token:**

```yaml
auth:
  type: "bearer"
  token: "${ES_TOKEN}"
```

### Environment variables

Use `${VAR_NAME}` syntax in `clusters.yaml` to reference environment variables. Elasticode will raise a clear error if a referenced variable is not set.

### TLS configuration

```yaml
tls:
  verify: true           # Enable/disable certificate verification
  ca_cert: "/path/to/ca.pem"  # Custom CA certificate (optional)
```

## CI/CD Usage

```bash
# Detect drift (exits 2 if changes needed)
elasticode plan --cluster production -o json

# Apply with auto-approve
elasticode apply --cluster production --auto-approve
```

## Development

See [docs/development.md](docs/development.md) for setup instructions.

## License

MIT
