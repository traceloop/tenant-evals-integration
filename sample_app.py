#!/usr/bin/env python3
"""
Sample application demonstrating the full evals-cli workflow.

This script walks through:
1. Creating an organization (with prd environment)
2. Creating a monitor setup for a workflow
3. Checking monitoring status
4. Retrieving metrics

Usage:
    uv run python sample_app.py

Or run individual steps:
    uv run python sample_app.py --step 1  # Create org only
    uv run python sample_app.py --step 2  # Create monitor setup
    uv run python sample_app.py --step 3  # Check status
    uv run python sample_app.py --step 4  # Get metrics
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from evals_cli.api import (
    APIError,
    AutoMonitorSetupClient,
    MetricsClient,
    MonitoringClient,
    OrganizationClient,
)
from evals_cli.config import get_config

console = Console()


def get_clients():
    """Initialize all API clients."""
    config = get_config()
    base_url = config.get("base_url")
    auth_token = config.get("auth_token")

    if not base_url or not auth_token:
        console.print(
            "[red]Error: Please configure the CLI first with 'uv run evals-cli configure'[/red]"
        )
        sys.exit(1)

    return {
        "org": OrganizationClient(base_url, auth_token),
        "setup": AutoMonitorSetupClient(base_url, auth_token),
        "monitoring": MonitoringClient(base_url, auth_token),
        "metrics": MetricsClient(base_url, auth_token),
    }


def step1_create_organization(clients: dict) -> dict:
    """Step 1: Create an organization with prd environment."""
    console.print(Panel("[bold blue]Step 1: Creating Organization[/bold blue]"))
    console.print("Creating organization 'Demo Organization' with 'prd' environment...")

    try:
        result = clients["org"].create(
            org_name="Demo Organization",
            environments=["prd"],
        )

        console.print("[green]✓ Organization created successfully![/green]")
        console.print(f"  Organization ID: [cyan]{result.get('org_id')}[/cyan]")

        if result.get("environments"):
            for env in result["environments"]:
                console.print(
                    f"  Environment: [yellow]{env.get('slug')}[/yellow] - API Key: [dim]{env.get('api_key', 'N/A')[:20]}...[/dim]"
                )

        return result

    except APIError as e:
        if e.status_code == 403:
            console.print(
                "[yellow]⚠ Not authorized to create organizations. Skipping...[/yellow]"
            )
        else:
            console.print(f"[red]Error: {e.message}[/red]")
        return {}


def step2_create_monitor_setup(clients: dict) -> dict:
    """Step 2: Create a monitor setup for the pirate_tech_joke_generator workflow."""
    console.print(Panel("[bold blue]Step 2: Creating Monitor Setup[/bold blue]"))
    console.print(
        "Creating monitor setup for workflow 'pirate_tech_joke_generator' with char-count evaluator..."
    )

    try:
        result = clients["setup"].create(
            entity_type="workflow",
            entity_value="pirate_tech_joke_generator",
            evaluator_types=["char-count"],
        )

        console.print("[green]✓ Monitor setup created successfully![/green]")
        console.print(f"  Setup ID: [cyan]{result.get('id')}[/cyan]")
        console.print(f"  Entity Type: [yellow]{result.get('entity_type')}[/yellow]")
        console.print(f"  Entity Value: [yellow]{result.get('entity_value')}[/yellow]")
        console.print(f"  Status: [magenta]{result.get('status')}[/magenta]")

        if result.get("evaluators"):
            console.print("  Evaluators:")
            for ev in result["evaluators"]:
                console.print(f"    - {ev}")

        return result

    except APIError as e:
        console.print(f"[red]Error: {e.message}[/red]")
        return {}


def step3_check_monitoring_status(clients: dict) -> dict:
    """Step 3: Check the monitoring/evaluation pipeline status."""
    console.print(Panel("[bold blue]Step 3: Checking Monitoring Status[/bold blue]"))
    console.print("Fetching evaluation pipeline status...")

    try:
        result = clients["monitoring"].get_status()

        status = result.get("status", "UNKNOWN")
        status_colors = {
            "OK": "green",
            "DEGRADED": "yellow",
            "ERROR": "red",
        }
        color = status_colors.get(status, "white")

        console.print(f"[green]✓ Status retrieved successfully![/green]")
        console.print(f"  Status: [{color}]{status}[/{color}]")
        console.print(
            f"  Lag (seconds): [cyan]{result.get('lag_in_seconds', 'N/A')}[/cyan]"
        )
        console.print(
            f"  Lag (spans): [cyan]{result.get('lag_in_spans', 'N/A')}[/cyan]"
        )

        if result.get("evaluated_up_to"):
            console.print(
                f"  Evaluated up to: [dim]{result.get('evaluated_up_to')}[/dim]"
            )
        if result.get("latest_span_received"):
            console.print(
                f"  Latest span: [dim]{result.get('latest_span_received')}[/dim]"
            )

        if result.get("reasons"):
            console.print(f"  Reasons: [yellow]{', '.join(result['reasons'])}[/yellow]")

        return result

    except APIError as e:
        console.print(f"[red]Error: {e.message}[/red]")
        return {}


def step4_get_metrics(clients: dict, project_id: str = None) -> dict:
    """Step 4: Retrieve metrics data."""
    console.print(Panel("[bold blue]Step 4: Retrieving Metrics[/bold blue]"))

    # Default to last 7 days
    from_timestamp = int((datetime.now() - timedelta(days=7)).timestamp())
    to_timestamp = int(datetime.now().timestamp())

    # Use provided project_id or a placeholder
    project_id = project_id or os.environ.get("EVALS_PROJECT_ID", "demo-project")

    console.print(f"Fetching metrics for project '{project_id}'...")
    console.print(f"  Time range: last 7 days")

    try:
        result = clients["metrics"].get_metrics(
            project_id=project_id,
            from_timestamp_sec=from_timestamp,
            to_timestamp_sec=to_timestamp,
            limit=10,
        )

        console.print("[green]✓ Metrics retrieved successfully![/green]")

        metrics_data = result.get("metrics", {})
        data = metrics_data.get("data", [])

        if data:
            console.print(f"  Total results: [cyan]{metrics_data.get('total_results', len(data))}[/cyan]")
            console.print(f"  Points returned: [cyan]{metrics_data.get('total_points', 0)}[/cyan]")

            # Display first few metrics
            table = Table(title="Sample Metrics")
            table.add_column("Metric Name", style="cyan")
            table.add_column("Points", style="magenta")
            table.add_column("Latest Value", style="green")

            for metric in data[:5]:
                name = metric.get("metric_name", "N/A")
                points = metric.get("points", [])
                latest_value = points[0].get("numeric_value", "N/A") if points else "N/A"
                table.add_row(name, str(len(points)), str(latest_value))

            console.print(table)
        else:
            console.print("  [yellow]No metrics data found in the specified time range.[/yellow]")

        return result

    except APIError as e:
        console.print(f"[red]Error: {e.message}[/red]")
        return {}


def run_full_demo():
    """Run the complete demo workflow."""
    console.print(
        Panel(
            "[bold green]Evals CLI - Full Workflow Demo[/bold green]\n\n"
            "This demo will walk through all the main API routes:\n"
            "1. Create an organization\n"
            "2. Create a monitor setup\n"
            "3. Check monitoring status\n"
            "4. Retrieve metrics",
            title="Welcome",
        )
    )

    clients = get_clients()
    results = {}

    console.print()
    results["org"] = step1_create_organization(clients)

    console.print()
    time.sleep(1)  # Brief pause between steps
    results["setup"] = step2_create_monitor_setup(clients)

    console.print()
    time.sleep(1)
    results["status"] = step3_check_monitoring_status(clients)

    console.print()
    time.sleep(1)
    results["metrics"] = step4_get_metrics(clients)

    console.print()
    console.print(
        Panel(
            "[bold green]Demo Complete![/bold green]\n\n"
            "All steps have been executed. Check the output above for results.\n\n"
            "You can also run individual CLI commands:\n"
            "  [dim]uv run evals-cli org create -n 'My Org'[/dim]\n"
            "  [dim]uv run evals-cli setup create -t workflow -v my-workflow -T char-count[/dim]\n"
            "  [dim]uv run evals-cli monitoring status[/dim]\n"
            "  [dim]uv run evals-cli metrics list -p project-id --from 2024-01-01[/dim]",
            title="Summary",
        )
    )

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Sample application demonstrating the evals-cli workflow"
    )
    parser.add_argument(
        "--step",
        type=int,
        choices=[1, 2, 3, 4],
        help="Run a specific step only (1-4)",
    )
    parser.add_argument(
        "--project-id",
        help="Project ID for metrics (step 4)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )

    args = parser.parse_args()

    clients = get_clients()

    if args.step:
        step_functions = {
            1: lambda: step1_create_organization(clients),
            2: lambda: step2_create_monitor_setup(clients),
            3: lambda: step3_check_monitoring_status(clients),
            4: lambda: step4_get_metrics(clients, args.project_id),
        }

        result = step_functions[args.step]()

        if args.json:
            console.print(json.dumps(result, indent=2))
    else:
        results = run_full_demo()

        if args.json:
            console.print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
