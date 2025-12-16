# Sample Application

This sample application demonstrates the full workflow of using the evals CLI API clients.

## Overview

The `sample_app.py` script executes a 4-step workflow:

1. Create an organization
2. Create an auto-monitor setup
3. Check monitoring status
4. Fetch metrics

## Running the Application

```bash
python sample_app.py
```

## Configuration

Update these constants in `sample_app.py`:

```python
BASE_URL = "http://localhost:8080"
AUTH_TOKEN = "Bearer your-auth-token-here"
DEFAULT_PROJECT = "default"
```

## API Routes and Payloads

### 1. Create Organization

**Route:** `POST /v2/organizations`

**Headers:**
```json
{
  "Authorization": "Bearer your-auth-token-here",
  "Content-Type": "application/json"
}
```

**Payload:**
```json
{
  "org_name": "Demo Organization",
  "envs": ["prd"]
}
```

**Response:**
```json
{
  "org_id": "uuid",
  "environments": [
    {
      "slug": "prd",
      "api_key": "tl_xxx"
    }
  ]
}
```

---

### 2. Create Auto-Monitor Setup

**Route:** `POST /v2/auto-monitor-setups`

**Headers:**
```json
{
  "Authorization": "tl_xxx",
  "Content-Type": "application/json"
}
```

**Payload:**
```json
{
  "entity_type": "workflow",
  "entity_value": "pirate_tech_joke_generator",
  "evaluators": [
    {
      "evaluator_type": "char-count"
    }
  ]
}
```

**Response:**
```json
{
  "id": "setup-uuid",
  "entity_type": "workflow",
  "entity_value": "pirate_tech_joke_generator",
  "evaluators": [...],
  "status": "pending"
}
```

---

### 3. Get Monitoring Status

**Route:** `GET /v2/monitoring/status`

**Headers:**
```json
{
  "Authorization": "tl_xxx",
  "Content-Type": "application/json"
}
```

**Payload:** None (GET request)

**Response:**
```json
{
  "organization_id": "uuid",
  "environment": "prd",
  "project": "default",
  "evaluated_up_to": 1702500000,
  "latest_span_received": 1702500100,
  "lag_in_seconds": 100,
  "lag_in_spans": 5,
  "status": "OK",
  "reasons": []
}
```

**Status Values:**
- `OK` - Evaluation pipeline is healthy
- `DEGRADED` - Pipeline is experiencing delays
- `ERROR` - Pipeline has errors

---

### 4. Get Metrics

**Route:** `GET /v2/metrics`

**Headers:**
```json
{
  "Authorization": "tl_xxx",
  "Content-Type": "application/json"
}
```

**Query Parameters:**
```
?from_timestamp_sec=1701900000&to_timestamp_sec=1702500000&sort_by=event_time&sort_order=DESC&limit=10&cursor=0&logical_operator=AND
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `from_timestamp_sec` | int64 | Yes | Start timestamp in seconds |
| `to_timestamp_sec` | int64 | Yes | End timestamp in seconds |
| `environments` | []string | No | List of environments |
| `metric_name` | string | No | Filter by specific metric name |
| `metric_source` | string | No | Filter by metric source |
| `sort_by` | string | No | Sort field (default: event_time) |
| `sort_order` | string | No | ASC or DESC (default: DESC) |
| `limit` | int | No | Number of results (default: 50) |
| `cursor` | int64 | No | Cursor for pagination |
| `filters` | JSON string | No | JSON-encoded filter conditions |
| `logical_operator` | string | No | AND or OR for combining filters |

**Example with filters:**
```
?from_timestamp_sec=1701900000&to_timestamp_sec=1702500000&metric_name=char-count&filters=[{"field":"workflow","operator":"eq","value":"pirate_tech_joke_generator"}]
```

**Response:**
```json
{
  "metrics": {
    "data": [
      {
        "metric_name": "char-count",
        "points": [
          {
            "numeric_value": 150,
            "event_time": 1702500000000,
            "labels": {
              "metric_type": "counter",
              "environment": "prd",
              "trace_id": "abc123"
            }
          }
        ]
      }
    ],
    "total_points": 10,
    "total_results": 100
  }
}
```

---

## Workflow Diagram

```
┌─────────────────────────┐
│  1. Create Organization │
│  POST /v2/organizations │
└───────────┬─────────────┘
            │ Returns API key
            ▼
┌─────────────────────────────┐
│  2. Create Auto-Monitor     │
│  POST /v2/auto-monitor-setups│
└───────────┬─────────────────┘
            │
            ▼
┌─────────────────────────────┐
│  3. Check Monitoring Status │
│  GET /v2/monitoring/status  │
└───────────┬─────────────────┘
            │
            ▼
┌─────────────────────────┐
│  4. Fetch Metrics       │
│  GET /v2/metrics        │
└─────────────────────────┘
```

## Error Handling

All API clients raise `APIError` for HTTP errors (status code >= 400):

```python
from evals_cli.api import APIError

try:
    result = client.get_status()
except APIError as e:
    print(f"Error {e.status_code}: {e.message}")
```
