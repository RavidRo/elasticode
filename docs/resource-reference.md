# Resource File Reference

Elasticode manages Elasticsearch resources using JSON files organized by type.

## Directory structure

```
your-project/
├── clusters.yaml
├── index_templates/
│   ├── logs.json
│   └── metrics.json
├── component_templates/
│   ├── base-settings.json
│   └── base-mappings.json
├── ilm_policies/
│   ├── hot-warm-cold.json
│   └── delete-after-30d.json
└── ingest_pipelines/
    ├── parse-logs.json
    └── enrich-data.json
```

## Naming convention

- **Filename** (without `.json`) = **resource name** in Elasticsearch
- Use lowercase with hyphens: `my-template.json` creates a resource named `my-template`
- The file content is the resource body exactly as the Elasticsearch API expects it

## Index Templates

**Directory:** `index_templates/`

**Elasticsearch API:** `PUT _index_template/<name>`

The file content is the request body for the [Put Index Template API](https://www.elastic.co/guide/en/elasticsearch/reference/current/indices-put-template.html).

```json
{
  "index_patterns": ["logs-*"],
  "priority": 100,
  "composed_of": ["base-settings", "base-mappings"],
  "template": {
    "settings": {
      "number_of_shards": 1,
      "number_of_replicas": 1,
      "index.lifecycle.name": "logs-lifecycle"
    },
    "mappings": {
      "properties": {
        "@timestamp": { "type": "date" },
        "message": { "type": "text" },
        "level": { "type": "keyword" },
        "host": { "type": "keyword" }
      }
    },
    "aliases": {
      "logs-all": {}
    }
  }
}
```

**Key fields:**
- `index_patterns` (required) -- which indices this template applies to
- `priority` -- higher priority templates take precedence
- `composed_of` -- list of component template names to compose
- `template` -- settings, mappings, and aliases

## Component Templates

**Directory:** `component_templates/`

**Elasticsearch API:** `PUT _component_template/<name>`

Component templates are reusable building blocks composed into index templates.

```json
{
  "template": {
    "mappings": {
      "properties": {
        "@timestamp": { "type": "date" },
        "host": { "type": "keyword" },
        "environment": { "type": "keyword" }
      }
    }
  }
}
```

**Key fields:**
- `template` -- contains settings, mappings, and/or aliases

## ILM Policies

**Directory:** `ilm_policies/`

**Elasticsearch API:** `PUT _ilm/policy/<name>`

Index Lifecycle Management policies define how indices transition through phases.

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
          },
          "set_priority": {
            "priority": 100
          }
        }
      },
      "warm": {
        "min_age": "7d",
        "actions": {
          "shrink": {
            "number_of_shards": 1
          },
          "forcemerge": {
            "max_num_segments": 1
          },
          "set_priority": {
            "priority": 50
          }
        }
      },
      "cold": {
        "min_age": "30d",
        "actions": {
          "set_priority": {
            "priority": 0
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

**Server-managed fields** (excluded from diffs automatically):
- `version` -- incremented by ES on each update
- `modified_date` / `modified_date_millis` -- last modification timestamp
- `in_use_by` -- which indices use this policy

## Ingest Pipelines

**Directory:** `ingest_pipelines/`

**Elasticsearch API:** `PUT _ingest/pipeline/<name>`

Ingest pipelines define a sequence of processors to transform documents before indexing.

```json
{
  "description": "Parse application log messages",
  "processors": [
    {
      "grok": {
        "field": "message",
        "patterns": [
          "%{TIMESTAMP_ISO8601:timestamp} %{LOGLEVEL:level} %{GREEDYDATA:msg}"
        ]
      }
    },
    {
      "date": {
        "field": "timestamp",
        "formats": ["ISO8601"],
        "target_field": "@timestamp"
      }
    },
    {
      "remove": {
        "field": "timestamp"
      }
    }
  ],
  "on_failure": [
    {
      "set": {
        "field": "_index",
        "value": "failed-logs"
      }
    }
  ]
}
```

**Key fields:**
- `description` -- human-readable description
- `processors` -- ordered list of processor definitions
- `on_failure` -- processors to run if the pipeline fails

## Normalization

When comparing local files against the cluster state, Elasticode strips server-managed fields that would cause false diffs. Each resource type has specific fields that are excluded:

| Resource Type | Stripped Fields |
|---|---|
| Index templates | `version` |
| Component templates | `version` |
| ILM policies | `version`, `modified_date`, `modified_date_millis`, `in_use_by` |
| Ingest pipelines | `version` |

If you include these fields in your JSON files, they will be sent to Elasticsearch but ignored during diff comparison.
