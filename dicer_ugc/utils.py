"""Common utilities for the pipeline."""

import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Union
import yaml
from rich.console import Console

console = Console()


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent


def get_output_dir(run_id: Optional[str] = None) -> Path:
    """Get output directory for a run."""
    base_dir = get_project_root() / "output"
    if run_id:
        return base_dir / run_id
    return base_dir


def get_cache_dir() -> Path:
    """Get cache directory."""
    return get_project_root() / "cache"


def get_face_cache_dir() -> Path:
    """Get face model cache directory."""
    return get_cache_dir() / "faces"


def get_audio_cache_dir(run_id: str) -> Path:
    """Get audio cache directory for a run."""
    return get_cache_dir() / "audio" / run_id


def generate_run_id() -> str:
    """Generate a unique run ID with timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"run_{timestamp}"


def hash_config(config_dict: dict) -> str:
    """Generate hash of configuration for change detection."""
    # Sort keys for consistent hashing
    config_str = yaml.dump(config_dict, sort_keys=True)
    return hashlib.sha256(config_str.encode()).hexdigest()[:16]


def ensure_dir(path: Union[str, Path]) -> Path:
    """Ensure directory exists."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_env_var(key: str, default: Optional[str] = None, required: bool = True) -> Optional[str]:
    """Get environment variable with validation."""
    value = os.environ.get(key, default)
    if required and not value:
        raise ValueError(f"Environment variable {key} is required but not set")
    return value


def format_cost(amount: float) -> str:
    """Format cost for display."""
    return f"${amount:.2f}"


def format_duration(seconds: float) -> str:
    """Format duration for display."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def safe_filename(text: str, max_length: int = 50) -> str:
    """Convert text to safe filename."""
    # Remove/replace unsafe characters
    safe_text = text.lower()
    safe_text = safe_text.replace(' ', '_')
    safe_text = ''.join(c for c in safe_text if c.isalnum() or c in '_-')
    
    # Truncate if needed
    if len(safe_text) > max_length:
        safe_text = safe_text[:max_length]
    
    return safe_text


def read_script_content(script_path_or_text: Union[Path, str]) -> str:
    """Read script content from file or return inline text."""
    if isinstance(script_path_or_text, Path):
        with open(script_path_or_text, 'r', encoding='utf-8') as f:
            return f.read().strip()
    else:
        # Assume it's inline text
        return script_path_or_text.strip()


def write_manifest(output_dir: Path, data: dict) -> Path:
    """Write manifest JSON file."""
    manifest_path = output_dir / "manifest.json"
    with open(manifest_path, 'w') as f:
        import json
        json.dump(data, f, indent=2, default=str)
    return manifest_path


def log_progress(current: int, total: int, prefix: str = "Progress") -> None:
    """Log progress to console."""
    percentage = (current / total) * 100
    console.print(f"[cyan]{prefix}:[/cyan] {current}/{total} ({percentage:.1f}%)")


def log_error(message: str, error: Optional[Exception] = None) -> None:
    """Log error to console."""
    console.print(f"[red]ERROR:[/red] {message}")
    if error:
        console.print(f"[dim]{type(error).__name__}: {str(error)}[/dim]")


def log_success(message: str) -> None:
    """Log success to console."""
    console.print(f"[green]✓[/green] {message}")


def log_warning(message: str) -> None:
    """Log warning to console."""
    console.print(f"[yellow]⚠[/yellow] {message}")


def log_info(message: str) -> None:
    """Log info to console."""
    console.print(f"[blue]ℹ[/blue] {message}")