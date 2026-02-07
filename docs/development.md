# Development Guide

## Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

## Setup

```bash
# Clone the repository
git clone https://github.com/ravidrom/elasticode.git
cd elasticode

# Install dependencies (including dev tools)
uv sync
```

## Running the CLI locally

```bash
uv run elasticode --help
uv run elasticode init --directory /tmp/test-project
uv run elasticode validate --config /tmp/test-project/clusters.yaml
```

## Tests

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run a specific test file
uv run pytest tests/test_config.py

# Run with coverage
uv run pytest --cov=elasticode --cov-report=term-missing

# Skip integration tests (default)
uv run pytest -m "not integration"
```

## Type checking

```bash
uv run mypy src/
```

Elasticode uses mypy in strict mode. All source code must be fully typed.

## Linting and formatting

```bash
# Check for lint issues
uv run ruff check src/ tests/

# Auto-fix fixable issues
uv run ruff check src/ tests/ --fix

# Format code
uv run ruff format src/ tests/
```

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
