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

**Route:** `POST /v2/metrics`

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
  "from_timestamp_sec": 1701900000,
  "to_timestamp_sec": 1702500000,
  "environments": [],
  "sort_by": "event_time",
  "sort_order": "DESC",
  "limit": 10,
  "cursor": 0,
  "logical_operator": "AND"
}
```

**Optional Payload Fields:**
```json
{
  "metric_name": "char-count",
  "metric_source": "openllmetry",
  "value_type": "numeric",
  "filters": [
    {
      "field": "workflow",
      "operator": "eq",
      "value": "pirate_tech_joke_generator"
    }
  ]
}
```

**Response:**
```json
{
  "data": [
    {
      "metric_name": "char-count",
      "metric_source": "openllmetry",
      "event_time": 1702500000,
      "numeric_value": 150,
      "string_value": null,
      "metadata": {}
    }
  ],
  "cursor": 10,
  "has_more": false
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
│  POST /v2/metrics       │
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
