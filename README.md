# Evals CLI

A command-line tool for managing auto-monitor-setups and evaluations.

## Installation

```bash
# Install dependencies with uv
uv sync

# Or install in development mode
uv pip install -e .
```

## Configuration

Configure the CLI with your API credentials:

```bash
uv run evals-cli configure
```

Or set environment variables:

```bash
export EVALS_API_BASE_URL=http://localhost:8080
export EVALS_API_AUTH_TOKEN=Bearer your-token-here
```

You can also create a `.env` file based on `.env.example`.

## Usage

### Auto-Monitor Setups

**Create a new setup:**

```bash
# Using an existing evaluator ID
uv run evals-cli setup create -t agent -v my-agent-name -e cmf2mpzh4002401zwcz9y0gke

# Using an evaluator type (creates new evaluator)
uv run evals-cli setup create -t agent -v my-agent-name -T hallucination

# Multiple evaluators
uv run evals-cli setup create -t agent -v my-agent-name -e eval-id-1 -e eval-id-2 -T toxicity
```

**List setups:**

```bash
# List all
uv run evals-cli setup list

# Filter by entity type
uv run evals-cli setup list --entity-type agent

# Filter by status
uv run evals-cli setup list --status pending

# Output as JSON
uv run evals-cli setup list --json
```

**Get a specific setup:**

```bash
uv run evals-cli setup get <setup-id>
```

**Delete a setup:**

```bash
# With confirmation prompt
uv run evals-cli setup delete <setup-id>

# Skip confirmation
uv run evals-cli setup delete <setup-id> --yes
```

### Monitoring

**Get pipeline status:**

```bash
# Formatted output with color-coded status
uv run evals-cli monitoring status

# Output as JSON
uv run evals-cli monitoring status --json
```

The status command shows:
- **Status**: `OK` (lag <= 3min), `DEGRADED` (3-10min lag), or `ERROR` (>10min lag or no data)
- **Lag in seconds**: Time since last evaluation
- **Lag in spans**: Number of spans not yet evaluated
- **Reasons**: Why status is non-OK (e.g., `LAG_HIGH`, `NO_EVALUATION_DATA`)

### Metrics

**List metrics:**

```bash
# Get metrics from a specific date
uv run evals-cli metrics list -p my-project --from 2024-01-01

# Filter by metric name and environment
uv run evals-cli metrics list -p my-project --from 2024-01-01 -n llm.token.usage -e production

# Filter by metric source
uv run evals-cli metrics list -p my-project --from 2024-01-01 -s openllmetry

# Custom sorting and limit
uv run evals-cli metrics list -p my-project --from 2024-01-01 --sort-by numeric_value --sort-order DESC --limit 100

# Output as JSON
uv run evals-cli metrics list -p my-project --from 2024-01-01 --json
```

Options:
- `--project-id, -p` (required): Project ID
- `--from` (required): Start timestamp (epoch seconds or YYYY-MM-DD)
- `--to`: End timestamp (defaults to now)
- `--environment, -e`: Filter by environment (can specify multiple)
- `--metric-name, -n`: Filter by specific metric name
- `--metric-source, -s`: Filter by source (e.g., 'openllmetry')
- `--sort-by`: Sort field (event_time, metric_name, numeric_value)
- `--sort-order`: ASC or DESC (default: DESC)
- `--limit, -l`: Max results (default: 50)
- `--json`: Output raw JSON

### Organizations

**Create an organization:**

```bash
# Create with default environment (prd)
uv run evals-cli org create -n "My Organization"

# Create with multiple environments
uv run evals-cli org create -n "My Organization" -e dev -e staging -e prd

# Output as JSON
uv run evals-cli org create -n "My Organization" --json
```

Options:
- `--name, -n` (required): Organization name
- `--env, -e`: Environment slug (can specify multiple, defaults to 'prd')
- `--json`: Output raw JSON

The response includes the organization ID and API keys for each environment.

### Demo Mode

Run an interactive demonstration of all API routes:

```bash
uv run evals-cli demo
```

This will walk through creating, listing, retrieving, and testing the auto-monitor-setup endpoints.

### Sample Application

A complete sample application is included that demonstrates the full workflow:

```bash
# Run the full demo (all 4 steps)
uv run python sample_app.py

# Run individual steps
uv run python sample_app.py --step 1  # Create organization
uv run python sample_app.py --step 2  # Create monitor setup
uv run python sample_app.py --step 3  # Check monitoring status
uv run python sample_app.py --step 4  # Get metrics

# With JSON output
uv run python sample_app.py --json
```

The sample app walks through:
1. **Create Organization** - Creates "Demo Organization" with prd environment
2. **Create Monitor Setup** - Sets up monitoring for `pirate_tech_joke_generator` workflow with `char-count` evaluator
3. **Check Status** - Retrieves evaluation pipeline status
4. **Get Metrics** - Fetches metrics from the last 7 days

## API Routes

The CLI interacts with the following API endpoints:

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v2/auto-monitor-setups` | Create a new auto-monitor-setup |
| GET | `/v2/auto-monitor-setups` | List all setups (with optional filters) |
| GET | `/v2/auto-monitor-setups/:id` | Get a specific setup by ID |
| DELETE | `/v2/auto-monitor-setups/:id` | Delete a setup |
| GET | `/v2/monitoring/status` | Get evaluation pipeline status |
| GET | `/v2/metrics` | Query metrics with filtering |
| POST | `/v2/organizations` | Create a new organization |

### Query Parameters (List)

- `entity_type` - Filter by entity type (e.g., `agent`)
- `status` - Filter by status (e.g., `pending`, `active`)

### Create Payload

```json
{
  "entity_type": "agent",
  "entity_value": "my-agent-name",
  "evaluators": [
    { "evaluator_id": "existing-evaluator-id" },
    { "evaluator_type": "hallucination" }
  ]
}
```

Note: Each evaluator must have either `evaluator_id` OR `evaluator_type`, not both.

### Monitoring Status Response

```json
{
  "organization_id": "org-123",
  "environment": "production",
  "project": "my-project",
  "evaluated_up_to": "2024-01-15T10:30:00Z",
  "latest_span_received": "2024-01-15T10:32:00Z",
  "lag_in_seconds": 120,
  "lag_in_spans": 45,
  "status": "OK",
  "reasons": []
}
```

Status values:
- `OK` - Lag <= 3 minutes
- `DEGRADED` - Lag between 3-10 minutes
- `ERROR` - Lag > 10 minutes or no evaluation data

Possible reasons:
- `LAG_HIGH` - Evaluation lag exceeds threshold
- `NO_EVALUATION_DATA` - No evaluation data available but spans exist

### Metrics Request/Response

**Query Parameters:**
```
GET /v2/metrics?from_timestamp_sec=1702900000&to_timestamp_sec=1702986400&environments=production&metric_name=llm.token.usage&metric_source=openllmetry&sort_by=event_time&sort_order=DESC&limit=50
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

**Response:**
```json
{
  "metrics": {
    "data": [
      {
        "organization_id": "org-123",
        "metric_name": "llm.token.usage",
        "points": [
          {
            "numeric_value": 150.0,
            "event_time": 1702986400000,
            "labels": {
              "metric_type": "counter",
              "environment": "production",
              "trace_id": "abc123"
            }
          }
        ]
      }
    ],
    "total_points": 50,
    "total_results": 1234,
    "next_cursor": "1702986400000"
  }
}
```

### Create Organization Request/Response

**Request Body:**
```json
{
  "org_name": "My Organization",
  "envs": ["dev", "staging", "prd"]
}
```

**Response:**
```json
{
  "org_id": "uuid-string",
  "environments": [
    {"slug": "dev", "api_key": "tl_xxx..."},
    {"slug": "staging", "api_key": "tl_yyy..."},
    {"slug": "prd", "api_key": "tl_zzz..."}
  ]
}
