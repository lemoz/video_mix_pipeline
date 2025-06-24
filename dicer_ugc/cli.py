"""CLI interface for dicer-ugc."""

import typer
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
import json

from .config import load_config
from .runner import PipelineRunner
from .utils import get_output_dir, format_cost

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
    
    try:
        config = load_config(config_path)
        console.print(f"[green]✓[/green] Config loaded: {config.offer_id}")
        
        # Show estimated cost
        min_cost, max_cost = config.estimated_cost
        console.print(f"[dim]Estimated cost:[/dim] {format_cost(min_cost)} - {format_cost(max_cost)}")
        console.print(f"[dim]Cost cap:[/dim] {format_cost(config.cost_cap)}")
        
        if dry_run:
            console.print("[yellow]DRY RUN MODE - No API calls will be made[/yellow]")
        
        # Run pipeline
        runner = PipelineRunner(config, max_parallel=max_parallel)
        state = runner.run(dry_run=dry_run)
        
        if not dry_run:
            console.print(f"\n[green]✓[/green] Pipeline completed")
            console.print(f"[dim]Output directory:[/dim] {runner.output_dir}")
            
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


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
    
    try:
        # Load config from run directory
        run_dir = get_output_dir(run_id)
        config_path = run_dir / "config.yaml"
        
        if not config_path.exists():
            raise FileNotFoundError(f"No config found for run {run_id}")
        
        config = load_config(config_path)
        
        # Resume pipeline
        runner = PipelineRunner(config, run_id=run_id, max_parallel=max_parallel)
        state = runner.resume()
        
        console.print(f"\n[green]✓[/green] Resume completed")
        console.print(f"[dim]Total cost:[/dim] {format_cost(state.total_cost)}")
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


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
    try:
        # Find run directory
        if not run_id:
            # Get latest run
            output_base = get_output_dir()
            if output_base.exists():
                runs = sorted([d for d in output_base.iterdir() if d.is_dir() and d.name.startswith("run_")])
                if runs:
                    run_id = runs[-1].name
                else:
                    raise ValueError("No runs found")
            else:
                raise ValueError("No output directory found")
        
        console.print(f"[cyan]Cost report for run:[/cyan] {run_id}")
        
        # Load cost report
        run_dir = get_output_dir(run_id)
        cost_report_path = run_dir / "cost_report.json"
        
        if not cost_report_path.exists():
            raise FileNotFoundError(f"No cost report found for run {run_id}")
        
        with open(cost_report_path, 'r') as f:
            report = json.load(f)
        
        # Display summary table
        table = Table(title="Cost Summary")
        table.add_column("Provider", style="cyan")
        table.add_column("Cost (USD)", justify="right", style="green")
        
        for provider, cost in report["providers"].items():
            table.add_row(provider.capitalize(), format_cost(cost))
        
        table.add_row("", "")  # Empty row
        table.add_row("Total", format_cost(report["total_cost"]), style="bold")
        table.add_row("Cost Cap", format_cost(report["cost_cap"]), style="dim")
        
        console.print(table)
        
        if detailed:
            # Load detailed tracking
            tracking_path = run_dir / "cost_tracking.jsonl"
            if tracking_path.exists():
                console.print("\n[cyan]Detailed Cost Breakdown:[/cyan]")
                entries = []
                with open(tracking_path, 'r') as f:
                    for line in f:
                        entries.append(json.loads(line))
                
                detail_table = Table()
                detail_table.add_column("Time", style="dim")
                detail_table.add_column("Provider")
                detail_table.add_column("Operation")
                detail_table.add_column("Units", justify="right")
                detail_table.add_column("Cost", justify="right", style="green")
                
                for entry in entries[-20:]:  # Show last 20 entries
                    time_str = entry['timestamp'].split('T')[1][:8]
                    detail_table.add_row(
                        time_str,
                        entry['provider'],
                        entry['operation'],
                        str(entry['units']),
                        format_cost(entry['total_cost'])
                    )
                
                console.print(detail_table)
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


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
    
    try:
        config = load_config(config_path)
        console.print("[green]✓[/green] Configuration is valid")
        
        console.print(f"\n[dim]Offer ID:[/dim] {config.offer_id}")
        console.print(f"[dim]Reference video:[/dim] {config.reference.video}")
        console.print(f"[dim]Actors:[/dim] {len(config.actors)} ({', '.join(config.actors)})")
        
        console.print("\n[dim]Ready to generate:[/dim]")
        console.print(f"  • {len(config.actors)} actors")
        console.print(f"  • {1 + config.variants.minor_script_variants} variants per actor")
        console.print(f"  • {config.total_videos} total videos")
        
        min_cost, max_cost = config.estimated_cost
        console.print(f"  • Estimated cost: {format_cost(min_cost)}-{format_cost(max_cost)}")
        console.print(f"  • Cost cap: {format_cost(config.cost_cap)}")
        
    except Exception as e:
        console.print(f"[red]Invalid configuration:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def version():
    """Show version information."""
    from dicer_ugc import __version__
    console.print(f"dicer-ugc version {__version__}")


if __name__ == "__main__":
    app()