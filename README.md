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

### Demo Mode

Run an interactive demonstration of all API routes:

```bash
uv run evals-cli demo
```

This will walk through creating, listing, retrieving, and testing the auto-monitor-setup endpoints.

## API Routes

The CLI interacts with the following API endpoints:

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v2/auto-monitor-setups` | Create a new auto-monitor-setup |
| GET | `/v2/auto-monitor-setups` | List all setups (with optional filters) |
| GET | `/v2/auto-monitor-setups/:id` | Get a specific setup by ID |
| DELETE | `/v2/auto-monitor-setups/:id` | Delete a setup |
| GET | `/v2/monitoring/status` | Get evaluation pipeline status |

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
