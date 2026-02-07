# Development Guide

## Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- [Task](https://taskfile.dev/) (optional, for running common commands via `Taskfile.yml`)

## Setup

```bash
# Clone the repository
git clone https://github.com/ravidrom/elasticode.git
cd elasticode

# Install dependencies (including dev tools)
task install
# or: uv sync
```

## Taskfile

The project includes a `Taskfile.yml` for common contributor workflows. Run `task --list` to see all available tasks:

| Command | Description |
|---|---|
| `task install` | Install all dependencies (including dev tools) |
| `task test` | Run the test suite |
| `task test:verbose` | Run tests with verbose output |
| `task test:cov` | Run tests with coverage report |
| `task lint` | Run ruff linter |
| `task lint:fix` | Auto-fix linting issues |
| `task format` | Format code with ruff |
| `task format:check` | Check formatting without applying changes |
| `task typecheck` | Run mypy strict type checking |
| `task check` | Run all checks (lint, typecheck, format, tests) |
| `task run` | Run the elasticode CLI |
| `task dev:up` | Start local Elasticsearch and Kibana |

Most tasks accept extra arguments via `--`, for example: `task test -- tests/test_config.py -v`

## Running the CLI locally

```bash
task run -- --help
task run -- init --directory /tmp/test-project
# or directly: uv run elasticode --help
```

## Tests

```bash
task test                          # Run all tests
task test:verbose                  # Verbose output
task test -- tests/test_config.py  # Specific file
task test:cov                      # With coverage report
```

Skip integration tests (default): `task test -- -m "not integration"`

## Type checking

```bash
task typecheck
```

Elasticode uses mypy in strict mode. All source code must be fully typed. Tests are also type-checked but with relaxed rules.

## Linting and formatting

```bash
task lint         # Check for lint issues
task lint:fix     # Auto-fix fixable issues
task format       # Format code
task format:check # Check without applying
```

## Run all checks at once

```bash
task check
```

This runs lint, typecheck, format check, and tests in parallel, then reports results.

## Local development with Docker

For testing against a real Elasticsearch cluster, the project includes a docker-compose setup with Elasticsearch 8.17.0 and Kibana.

### Start the local cluster

```bash
task dev:up
```

This starts Elasticsearch on port 9200 and Kibana on port 5601. Wait for the health checks to pass (about 30 seconds).

### Test Elasticode against the local cluster

Create a test `clusters.yaml`:

```yaml
clusters:
  local:
    url: http://localhost:9200
    auth:
      type: basic
      username: elastic
      password: changeme
    tls:
      verify: false
```

Then run Elasticode commands:

```bash
# Initialize a test project
task run -- init --directory /tmp/elasticode-test
cd /tmp/elasticode-test

# Create the clusters.yaml with the local config above
# Add some test resources to index_templates/, ilm_policies/, etc.

# Plan changes
task run -- plan --cluster local --config clusters.yaml

# Apply changes
task run -- apply --cluster local --config clusters.yaml
```

### View logs

```bash
task dev:logs              # Follow all logs
task dev:logs -- elasticsearch  # Just ES logs
task dev:logs -- kibana         # Just Kibana logs
```

### Check cluster status

```bash
task dev:status
```

### Stop the cluster

```bash
task dev:down
```

### Access Kibana

Open http://localhost:5601 in your browser and log in with:
- Username: `elastic`
- Password: `changeme`

## Project structure

```
src/elasticode/
    cli.py          # Click CLI entry point and commands
    config.py       # Cluster config loading, env var interpolation
    client.py       # Elasticsearch client factory
    loader.py       # Resource file discovery and JSON parsing
    differ.py       # Diff engine (desired vs current state)
    planner.py      # Plan generation orchestrator
    applier.py      # Plan execution against cluster
    output.py       # Rich terminal output formatting
    errors.py       # Exception hierarchy
    types.py        # Shared dataclasses and enums
    scaffold.py     # Project scaffolding for `init` command
    resources/
        base.py             # Abstract ResourceHandler
        index_template.py   # Index template handler
        component_template.py
        ilm_policy.py
        ingest_pipeline.py
```

## Adding a new resource type

1. Create a new handler in `src/elasticode/resources/` extending `ResourceHandler`
2. Implement `resource_type`, `directory_name`, `get`, `put`, `delete`, and `normalize`
3. Add the handler to `HANDLER_CLASSES` in `src/elasticode/resources/__init__.py`
4. Add the new type to the `ResourceType` enum in `src/elasticode/types.py`
5. Add tests in `tests/resources/`
6. Add test fixtures in `tests/fixtures/<directory_name>/`

The CLI automatically picks up new resource types from the `ResourceType` enum -- no CLI code changes needed.

## Architecture

The core pipeline is: **Load -> Diff -> Plan -> (Display | Apply)**

1. `config.py` loads `clusters.yaml` and interpolates `${ENV_VAR}` references
2. `client.py` creates an `Elasticsearch` client from the cluster config
3. `loader.py` discovers `.json` files in resource directories
4. Each resource's `ResourceHandler` fetches current state from Elasticsearch
5. `differ.py` compares desired vs current using `deepdiff`, after handler-specific `normalize()` strips server-managed fields
6. `planner.py` assembles a `Plan` object (list of create/update/no-change items)
7. `output.py` renders the plan with Rich (colored tables and diffs)
8. `applier.py` executes plan items via the appropriate handler's `put()` method
