"""CLI interface for dicer-ugc."""

import typer
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
import json

app = typer.Typer(
    name="dicer-ugc",
    help="UGC video variation pipeline",
    add_completion=False,
)
console = Console()


@app.command()
def run(
    config_path: Path = typer.Argument(
        ..., 
        help="Path to YAML configuration file",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    max_parallel: int = typer.Option(
        3, 
        "--max-parallel", 
        "-p",
        help="Maximum parallel API calls",
        min=1,
        max=10,
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Preview tasks without executing",
    ),
):
    """Run video generation pipeline from config file."""
    console.print(f"[cyan]Loading config from:[/cyan] {config_path}")
    
    if dry_run:
        console.print("[yellow]DRY RUN MODE - No API calls will be made[/yellow]")
    
    # TODO: Load config and run pipeline
    console.print("[green]✓[/green] Pipeline started")
    console.print(f"[dim]Max parallel tasks:[/dim] {max_parallel}")


@app.command()
def resume(
    run_id: str = typer.Argument(
        ..., 
        help="Run ID to resume"
    ),
    max_parallel: int = typer.Option(
        3, 
        "--max-parallel", 
        "-p",
        help="Maximum parallel API calls",
        min=1,
        max=10,
    ),
):
    """Resume an interrupted pipeline run."""
    console.print(f"[cyan]Resuming run:[/cyan] {run_id}")
    
    # TODO: Load state and resume
    console.print(f"[green]✓[/green] Resuming with {max_parallel} parallel tasks")


@app.command()
def cost(
    run_id: Optional[str] = typer.Argument(
        None,
        help="Run ID to analyze (latest if not specified)"
    ),
    detailed: bool = typer.Option(
        False,
        "--detailed",
        "-d",
        help="Show detailed breakdown",
    ),
):
    """Display cost report for a pipeline run."""
    if run_id:
        console.print(f"[cyan]Cost report for run:[/cyan] {run_id}")
    else:
        console.print("[cyan]Cost report for latest run[/cyan]")
    
    # TODO: Load and display cost report
    table = Table(title="Cost Summary")
    table.add_column("Provider", style="cyan")
    table.add_column("API Calls", justify="right")
    table.add_column("Cost (USD)", justify="right", style="green")
    
    # Example data
    table.add_row("ElevenLabs", "12", "$2.40")
    table.add_row("Gemini Vision", "36", "$0.72")
    table.add_row("Total", "48", "$3.12", style="bold")
    
    console.print(table)


@app.command()
def list_runs(
    limit: int = typer.Option(
        10,
        "--limit",
        "-n",
        help="Number of recent runs to show",
    ),
):
    """List recent pipeline runs."""
    console.print(f"[cyan]Recent runs (limit: {limit})[/cyan]\n")
    
    # TODO: List actual runs from output directory
    table = Table()
    table.add_column("Run ID", style="cyan")
    table.add_column("Date", style="dim")
    table.add_column("Status")
    table.add_column("Videos", justify="right")
    table.add_column("Cost", justify="right", style="green")
    
    # Example data
    table.add_row("run_20240315_142035", "2024-03-15 14:20", "[green]Complete[/green]", "12", "$3.12")
    table.add_row("run_20240315_091522", "2024-03-15 09:15", "[yellow]Partial[/yellow]", "8/12", "$2.08")
    
    console.print(table)


@app.command()
def validate(
    config_path: Path = typer.Argument(
        ..., 
        help="Path to YAML configuration file",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
):
    """Validate configuration file without running pipeline."""
    console.print(f"[cyan]Validating config:[/cyan] {config_path}")
    
    # TODO: Load and validate config
    console.print("[green]✓[/green] Configuration is valid")
    console.print("\n[dim]Ready to generate:[/dim]")
    console.print("  • 3 actors")
    console.print("  • 4 variants per actor")
    console.print("  • 12 total videos")
    console.print("  • Estimated cost: $3.00-$4.00")


@app.command()
def version():
    """Show version information."""
    from dicer_ugc import __version__
    console.print(f"dicer-ugc version {__version__}")


if __name__ == "__main__":
    app()