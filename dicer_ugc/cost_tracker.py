"""Cost tracking and enforcement."""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import json
from enum import Enum

from .utils import format_cost, log_warning, ensure_dir


class Provider(str, Enum):
    """Supported providers."""
    ELEVENLABS = "elevenlabs"
    GEMINI = "gemini"
    ARCADS = "arcads"
    REPLICATE = "replicate"


@dataclass
class CostEntry:
    """Single cost entry."""
    timestamp: datetime
    provider: Provider
    operation: str
    units: int  # Characters for TTS, tokens for LLM, etc.
    unit_cost: float
    total_cost: float
    task_id: Optional[str] = None
    metadata: Dict = field(default_factory=dict)


class CostTracker:
    """Track and enforce cost limits."""
    
    # Provider rate cards (example rates)
    PROVIDER_RATES = {
        Provider.ELEVENLABS: {
            "tts_per_character": 0.00015,
        },
        Provider.GEMINI: {
            "vision_per_token": 0.000002,  # Gemini 2.5 Vision
            "vision_per_image": 0.02,      # Fixed cost per image
        },
        Provider.ARCADS: {
            "avatar_generation": 5.0,  # Per avatar
        },
        Provider.REPLICATE: {
            "wav2lip_per_second": 0.01,  # Per second of video
        }
    }
    
    def __init__(self, cost_cap: float, output_dir: Optional[Path] = None):
        self.cost_cap = cost_cap
        self.output_dir = output_dir
        self.entries: List[CostEntry] = []
        self._total_by_provider: Dict[Provider, float] = {p: 0.0 for p in Provider}
        self._load_existing()
    
    def _load_existing(self):
        """Load existing cost data if resuming."""
        if self.output_dir:
            cost_file = self.output_dir / "cost_tracking.jsonl"
            if cost_file.exists():
                with open(cost_file, 'r') as f:
                    for line in f:
                        data = json.loads(line)
                        entry = CostEntry(
                            timestamp=datetime.fromisoformat(data['timestamp']),
                            provider=Provider(data['provider']),
                            operation=data['operation'],
                            units=data['units'],
                            unit_cost=data['unit_cost'],
                            total_cost=data['total_cost'],
                            task_id=data.get('task_id'),
                            metadata=data.get('metadata', {})
                        )
                        self.entries.append(entry)
                        self._total_by_provider[entry.provider] += entry.total_cost
    
    def _save_entry(self, entry: CostEntry):
        """Append entry to tracking file."""
        if self.output_dir:
            ensure_dir(self.output_dir)
            cost_file = self.output_dir / "cost_tracking.jsonl"
            with open(cost_file, 'a') as f:
                data = {
                    'timestamp': entry.timestamp.isoformat(),
                    'provider': entry.provider.value,
                    'operation': entry.operation,
                    'units': entry.units,
                    'unit_cost': entry.unit_cost,
                    'total_cost': entry.total_cost,
                    'task_id': entry.task_id,
                    'metadata': entry.metadata
                }
                f.write(json.dumps(data) + '\n')
    
    def track_cost(
        self,
        provider: Provider,
        operation: str,
        units: int,
        unit_cost: Optional[float] = None,
        task_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> float:
        """
        Track a cost entry.
        
        Returns:
            The cost of this operation
        
        Raises:
            CostCapExceeded if cap would be exceeded
        """
        # Get unit cost if not provided
        if unit_cost is None:
            if provider in self.PROVIDER_RATES and operation in self.PROVIDER_RATES[provider]:
                unit_cost = self.PROVIDER_RATES[provider][operation]
            else:
                raise ValueError(f"No rate defined for {provider}.{operation}")
        
        total_cost = units * unit_cost
        
        # Check if this would exceed cap
        new_total = self.get_total_cost() + total_cost
        if new_total > self.cost_cap:
            raise CostCapExceeded(
                f"Cost cap would be exceeded: {format_cost(new_total)} > {format_cost(self.cost_cap)}"
            )
        
        # Record entry
        entry = CostEntry(
            timestamp=datetime.now(),
            provider=provider,
            operation=operation,
            units=units,
            unit_cost=unit_cost,
            total_cost=total_cost,
            task_id=task_id,
            metadata=metadata or {}
        )
        
        self.entries.append(entry)
        self._total_by_provider[provider] += total_cost
        self._save_entry(entry)
        
        # Warn if getting close to cap
        if new_total > self.cost_cap * 0.8:
            log_warning(f"Cost approaching cap: {format_cost(new_total)} / {format_cost(self.cost_cap)}")
        
        return total_cost
    
    def track_tts(self, text: str, task_id: Optional[str] = None) -> float:
        """Track TTS generation cost."""
        return self.track_cost(
            provider=Provider.ELEVENLABS,
            operation="tts_per_character",
            units=len(text),
            task_id=task_id,
            metadata={"text_preview": text[:50] + "..." if len(text) > 50 else text}
        )
    
    def track_vision_eval(self, num_tokens: int, num_images: int = 1, task_id: Optional[str] = None) -> float:
        """Track Gemini vision evaluation cost."""
        token_cost = self.track_cost(
            provider=Provider.GEMINI,
            operation="vision_per_token",
            units=num_tokens,
            task_id=task_id
        )
        
        image_cost = self.track_cost(
            provider=Provider.GEMINI,
            operation="vision_per_image",
            units=num_images,
            task_id=task_id
        )
        
        return token_cost + image_cost
    
    def get_total_cost(self) -> float:
        """Get total cost across all providers."""
        return sum(self._total_by_provider.values())
    
    def get_provider_costs(self) -> Dict[Provider, float]:
        """Get costs broken down by provider."""
        return self._total_by_provider.copy()
    
    def get_remaining_budget(self) -> float:
        """Get remaining budget before cap."""
        return max(0, self.cost_cap - self.get_total_cost())
    
    def can_afford(self, estimated_cost: float) -> bool:
        """Check if an operation can be afforded."""
        return self.get_total_cost() + estimated_cost <= self.cost_cap
    
    def generate_report(self) -> Dict:
        """Generate detailed cost report."""
        provider_details = {}
        for provider in Provider:
            provider_entries = [e for e in self.entries if e.provider == provider]
            if provider_entries:
                provider_details[provider.value] = {
                    "total_cost": self._total_by_provider[provider],
                    "num_operations": len(provider_entries),
                    "operations": {}
                }
                
                # Group by operation
                for entry in provider_entries:
                    op = entry.operation
                    if op not in provider_details[provider.value]["operations"]:
                        provider_details[provider.value]["operations"][op] = {
                            "count": 0,
                            "total_units": 0,
                            "total_cost": 0.0
                        }
                    provider_details[provider.value]["operations"][op]["count"] += 1
                    provider_details[provider.value]["operations"][op]["total_units"] += entry.units
                    provider_details[provider.value]["operations"][op]["total_cost"] += entry.total_cost
        
        return {
            "total_cost": self.get_total_cost(),
            "cost_cap": self.cost_cap,
            "remaining_budget": self.get_remaining_budget(),
            "utilization_percent": (self.get_total_cost() / self.cost_cap * 100) if self.cost_cap > 0 else 0,
            "providers": provider_details,
            "num_entries": len(self.entries),
            "first_entry": self.entries[0].timestamp.isoformat() if self.entries else None,
            "last_entry": self.entries[-1].timestamp.isoformat() if self.entries else None,
        }


class CostCapExceeded(Exception):
    """Raised when cost cap would be exceeded."""
    pass