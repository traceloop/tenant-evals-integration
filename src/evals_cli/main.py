"""Main CLI entry point."""

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print_json

from .config import get_config, save_config
from .api import AutoMonitorSetupClient, MonitoringClient, APIError

console = Console()


def get_client() -> AutoMonitorSetupClient:
    """Get configured API client for auto-monitor-setups."""
    config = get_config()
    if not config["auth_token"]:
        console.print("[red]Error: No auth token configured.[/red]")
        console.print("Run [cyan]evals-cli configure[/cyan] to set up authentication.")
        raise click.Abort()
    return AutoMonitorSetupClient(config["base_url"], config["auth_token"])


def get_monitoring_client() -> MonitoringClient:
    """Get configured API client for monitoring."""
    config = get_config()
    if not config["auth_token"]:
        console.print("[red]Error: No auth token configured.[/red]")
        console.print("Run [cyan]evals-cli configure[/cyan] to set up authentication.")
        raise click.Abort()
    return MonitoringClient(config["base_url"], config["auth_token"])


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Evals CLI - Manage auto-monitor-setups and evaluations."""
    pass


@cli.command()
@click.option("--base-url", prompt="API Base URL", default="http://localhost:8080", help="Base URL for the API")
@click.option("--auth-token", prompt="Auth Token", hide_input=True, help="Authentication token")
def configure(base_url: str, auth_token: str):
    """Configure API connection settings."""
    save_config(base_url, auth_token)
    console.print("[green]Configuration saved successfully![/green]")


@cli.group()
def setup():
    """Manage auto-monitor-setups."""
    pass


@setup.command("create")
@click.option("--entity-type", "-t", required=True, help="Entity type (e.g., 'agent')")
@click.option("--entity-value", "-v", required=True, help="Entity value/name")
@click.option("--evaluator-id", "-e", multiple=True, help="Evaluator ID to use (can specify multiple)")
@click.option("--evaluator-type", "-T", multiple=True, help="Evaluator type to create (e.g., 'hallucination', 'toxicity')")
def setup_create(entity_type: str, entity_value: str, evaluator_id: tuple, evaluator_type: tuple):
    """Create a new auto-monitor-setup."""
    if not evaluator_id and not evaluator_type:
        console.print("[red]Error: Must specify at least one --evaluator-id or --evaluator-type[/red]")
        raise click.Abort()

    client = get_client()

    try:
        result = client.create(
            entity_type=entity_type,
            entity_value=entity_value,
            evaluator_ids=list(evaluator_id) if evaluator_id else None,
            evaluator_types=list(evaluator_type) if evaluator_type else None,
        )
        console.print(Panel("[green]Auto-monitor-setup created successfully![/green]", title="Success"))
        print_json(data=result)
    except APIError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise click.Abort()


@setup.command("list")
@click.option("--entity-type", "-t", help="Filter by entity type")
@click.option("--status", "-s", help="Filter by status (e.g., 'pending', 'active')")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def setup_list(entity_type: str, status: str, as_json: bool):
    """List auto-monitor-setups."""
    client = get_client()

    try:
        results = client.list(entity_type=entity_type, status=status)

        if as_json:
            print_json(data=results)
            return

        if not results:
            console.print("[yellow]No setups found.[/yellow]")
            return

        table = Table(title="Auto-Monitor Setups")
        table.add_column("ID", style="cyan")
        table.add_column("Entity Type", style="magenta")
        table.add_column("Entity Value", style="green")
        table.add_column("Status", style="yellow")
        table.add_column("Evaluators", style="blue")

        for setup in results:
            evaluators = setup.get("evaluators", [])
            evaluator_count = len(evaluators) if isinstance(evaluators, list) else 0
            table.add_row(
                setup.get("id", "N/A"),
                setup.get("entity_type", "N/A"),
                setup.get("entity_value", "N/A"),
                setup.get("status", "N/A"),
                str(evaluator_count),
            )

        console.print(table)
        console.print(f"\n[dim]Total: {len(results)} setup(s)[/dim]")
    except APIError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise click.Abort()


@setup.command("get")
@click.argument("setup_id")
def setup_get(setup_id: str):
    """Get details of a specific auto-monitor-setup."""
    client = get_client()

    try:
        result = client.get(setup_id)
        console.print(Panel(f"[cyan]Setup: {setup_id}[/cyan]", title="Auto-Monitor Setup"))
        print_json(data=result)
    except APIError as e:
        if e.status_code == 404:
            console.print(f"[red]Error: Setup '{setup_id}' not found.[/red]")
        else:
            console.print(f"[red]Error: {e}[/red]")
        raise click.Abort()


@setup.command("delete")
@click.argument("setup_id")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
def setup_delete(setup_id: str, yes: bool):
    """Delete an auto-monitor-setup."""
    if not yes:
        if not click.confirm(f"Are you sure you want to delete setup '{setup_id}'?"):
            console.print("[yellow]Cancelled.[/yellow]")
            return

    client = get_client()

    try:
        client.delete(setup_id)
        console.print(f"[green]Setup '{setup_id}' deleted successfully.[/green]")
    except APIError as e:
        if e.status_code == 404:
            console.print(f"[red]Error: Setup '{setup_id}' not found.[/red]")
        else:
            console.print(f"[red]Error: {e}[/red]")
        raise click.Abort()


@cli.group()
def monitoring():
    """View monitoring status and pipeline health."""
    pass


@monitoring.command("status")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def monitoring_status(as_json: bool):
    """Get monitoring status for the organization.

    Shows evaluation pipeline health including lag metrics and status.

    Status values:
      - OK: lag <= 3 minutes
      - DEGRADED: 3min < lag <= 10min
      - ERROR: lag > 10min or no evaluation data
    """
    client = get_monitoring_client()

    try:
        result = client.get_status()

        if as_json:
            print_json(data=result)
            return

        status = result.get("status", "UNKNOWN")
        status_color = {
            "OK": "green",
            "DEGRADED": "yellow",
            "ERROR": "red",
        }.get(status, "white")

        console.print(Panel(
            f"[bold {status_color}]{status}[/bold {status_color}]",
            title="Monitoring Status"
        ))

        table = Table(show_header=False, box=None)
        table.add_column("Field", style="dim")
        table.add_column("Value")

        table.add_row("Organization", result.get("organization_id", "N/A"))

        if result.get("environment"):
            table.add_row("Environment", result["environment"])
        if result.get("project"):
            table.add_row("Project", result["project"])

        table.add_row("", "")  # Spacer

        evaluated_up_to = result.get("evaluated_up_to")
        table.add_row("Evaluated Up To", evaluated_up_to or "[dim]N/A[/dim]")

        latest_span = result.get("latest_span_received")
        table.add_row("Latest Span Received", latest_span or "[dim]N/A[/dim]")

        table.add_row("", "")  # Spacer

        lag_seconds = result.get("lag_in_seconds", 0)
        lag_spans = result.get("lag_in_spans", 0)

        lag_color = "green" if lag_seconds <= 180 else ("yellow" if lag_seconds <= 600 else "red")
        table.add_row("Lag (seconds)", f"[{lag_color}]{lag_seconds}[/{lag_color}]")
        table.add_row("Lag (spans)", str(lag_spans))

        reasons = result.get("reasons", [])
        if reasons:
            table.add_row("", "")  # Spacer
            table.add_row("Reasons", ", ".join(reasons))

        console.print(table)

    except APIError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise click.Abort()


@cli.command()
def demo():
    """Run a demonstration of the auto-monitor-setup API routes."""
    config = get_config()

    console.print(Panel("[bold]Auto-Monitor Setup API Demo[/bold]", title="Evals CLI"))
    console.print()

    # Check configuration
    if not config["auth_token"]:
        console.print("[yellow]No auth token configured. Running in demo mode with prompts.[/yellow]")
        base_url = click.prompt("API Base URL", default="http://localhost:8080")
        auth_token = click.prompt("Auth Token", hide_input=True)
    else:
        base_url = config["base_url"]
        auth_token = config["auth_token"]
        console.print(f"[dim]Using configured API: {base_url}[/dim]")

    client = AutoMonitorSetupClient(base_url, auth_token)

    # Demo values
    entity_type = click.prompt("Entity type", default="agent")
    entity_value = click.prompt("Entity value")
    evaluator_id = click.prompt("Evaluator ID", default="cmf2mpzh4002401zwcz9y0gke")

    console.print()
    console.rule("[bold cyan]1. CREATE - POST /v2/auto-monitor-setups[/bold cyan]")

    try:
        result = client.create(
            entity_type=entity_type,
            entity_value=entity_value,
            evaluator_ids=[evaluator_id],
        )
        console.print("[green]Created successfully![/green]")
        print_json(data=result)
        setup_id = result.get("id")
    except APIError as e:
        console.print(f"[red]Failed: {e}[/red]")
        setup_id = None

    console.print()
    console.rule("[bold cyan]2. LIST - GET /v2/auto-monitor-setups[/bold cyan]")

    try:
        results = client.list()
        console.print(f"[green]Found {len(results)} setup(s)[/green]")
        print_json(data=results)
    except APIError as e:
        console.print(f"[red]Failed: {e}[/red]")

    console.print()
    console.rule("[bold cyan]3. LIST with filters[/bold cyan]")

    try:
        results = client.list(entity_type="agent", status="pending")
        console.print(f"[green]Found {len(results)} filtered setup(s)[/green]")
        print_json(data=results)
    except APIError as e:
        console.print(f"[red]Failed: {e}[/red]")

    if setup_id:
        console.print()
        console.rule(f"[bold cyan]4. GET BY ID - GET /v2/auto-monitor-setups/{setup_id}[/bold cyan]")

        try:
            result = client.get(setup_id)
            console.print("[green]Retrieved successfully![/green]")
            print_json(data=result)
        except APIError as e:
            console.print(f"[red]Failed: {e}[/red]")

    console.print()
    console.rule("[bold cyan]5. GET non-existent ID (404 test)[/bold cyan]")

    try:
        client.get("non-existent-id-12345")
        console.print("[yellow]Unexpected success[/yellow]")
    except APIError as e:
        if e.status_code == 404:
            console.print("[green]Correctly returned 404 for non-existent setup[/green]")
        else:
            console.print(f"[yellow]Unexpected error: {e}[/yellow]")

    console.print()
    console.rule("[bold cyan]Demo Complete[/bold cyan]")


if __name__ == "__main__":
    cli()
