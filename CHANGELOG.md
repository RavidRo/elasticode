# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `elasticode init` command to scaffold new projects with example files and directory structure
- `elasticode validate` command to check JSON resource files and cluster configuration
- `elasticode plan` command to preview changes with colored diff output (Terraform-like dry run)
- `elasticode apply` command to apply changes to clusters with confirmation prompt
- `elasticode export` command to fetch existing cluster resources and write them as local JSON files
- Support for 5 Elasticsearch resource types: index templates, component templates, ILM policies, ingest pipelines, and indices
- Create-only mode for indices to prevent accidental data loss (updates and deletes are blocked by default)
- Safety guardrails: indices cannot be updated in-place or deleted through Elasticode
- System indices (starting with `.`) are automatically filtered from export and list operations
- Multi-cluster support via `clusters.yaml` configuration file
- Environment variable interpolation (`${ENV_VAR}`) in cluster configuration
- Three authentication methods: basic auth, API key, and bearer token
- TLS configuration with optional CA certificate and verification toggle
- JSON output format for plan command (`-o json`) for CI/CD integration
- Resource type (`-t`) and resource name (`-r`) filtering across all commands
- Auto-approve flag (`-y`) for non-interactive apply in CI/CD pipelines
- Rich terminal output with colored diffs and summary tables
- Dockerfile for containerized usage
