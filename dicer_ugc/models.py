"""Shared data models for the pipeline."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any
import hashlib
import json


class VariantType(str, Enum):
    """Type of script variant."""
    IDENTICAL = "identical"
    MODIFIED = "modified"


class TaskStatus(str, Enum):
    """Status of a generation task."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class RubricDecision(str, Enum):
    """Rubric evaluation decision."""
    ACCEPT = "accept"
    REVIEW = "review"
    REJECT = "reject"


@dataclass
class Actor:
    """Actor information."""
    name: str
    scene_id: str
    voice_id: Optional[str] = None  # ElevenLabs voice ID
    style: Optional[str] = None  # e.g., "energetic", "calm", "professional"


@dataclass
class OfferMetadata:
    """Product/offer information for context."""
    name: str
    industry: str
    category: str
    description: str
    key_features: List[str]
    brand_elements: List[str]
    ideal_angles: List[str]
    important_details: List[str]
    avoid_showing: List[str]
    competitors: List[str]


@dataclass
class VariantTask:
    """Represents a single video generation task."""
    task_id: str
    actor: Actor
    variant_type: VariantType
    variant_num: int
    script_text: Optional[str] = None
    offer_metadata: Optional[OfferMetadata] = None
    
    def __post_init__(self):
        if not self.task_id:
            # Generate deterministic ID if not provided
            content = f"{self.actor.name}_{self.variant_type}_{self.variant_num}"
            self.task_id = hashlib.md5(content.encode()).hexdigest()[:12]
    
    @property
    def output_filename(self) -> str:
        """Generate consistent output filename."""
        return f"{self.actor.name}_{self.variant_type}_{self.variant_num:02d}.mp4"
    
    @property
    def actor_id(self) -> str:
        """Backward compatibility for actor ID."""
        return self.actor.name


@dataclass
class VideoOutputs:
    """Video pipeline outputs."""
    ugc_video: Optional[Path] = None
    broll_video: Optional[Path] = None
    captioned_video: Optional[Path] = None
    timeline_json: Optional[Path] = None
    
    @property
    def final_video(self) -> Optional[Path]:
        """Get the most processed video available."""
        return self.captioned_video or self.broll_video or self.ugc_video


@dataclass
class TaskResult:
    """Result of a generation task."""
    task_id: str
    status: TaskStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    outputs: Dict[str, Path] = field(default_factory=dict)
    video_outputs: Optional[VideoOutputs] = None
    costs: Dict[str, float] = field(default_factory=dict)
    
    @property
    def duration(self) -> Optional[float]:
        """Task duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    @property
    def total_cost(self) -> float:
        """Total cost across all providers."""
        return sum(self.costs.values())


@dataclass
class RubricEvaluation:
    """Single rubric evaluation result."""
    model_id: str
    temperature: float
    lip_sync: str
    tone: str
    script_alignment: str
    brand_compliance: str
    overall: str
    raw_response: Optional[str] = None
    
    @property
    def decision(self) -> RubricDecision:
        """Convert overall rating to decision."""
        if self.overall in ["excellent", "good"]:
            return RubricDecision.ACCEPT
        elif self.overall == "fair":
            return RubricDecision.REVIEW
        else:
            return RubricDecision.REJECT


@dataclass
class RubricResult:
    """Ensemble rubric evaluation result."""
    task_id: str
    evaluations: List[RubricEvaluation]
    final_decision: RubricDecision
    timestamp: datetime = field(default_factory=datetime.now)
    
    @classmethod
    def from_evaluations(cls, task_id: str, evaluations: List[RubricEvaluation]) -> 'RubricResult':
        """Create result from evaluations with majority voting."""
        decisions = [eval.decision for eval in evaluations]
        # Simple majority voting
        decision_counts = {
            RubricDecision.ACCEPT: decisions.count(RubricDecision.ACCEPT),
            RubricDecision.REVIEW: decisions.count(RubricDecision.REVIEW),
            RubricDecision.REJECT: decisions.count(RubricDecision.REJECT),
        }
        final_decision = max(decision_counts.items(), key=lambda x: x[1])[0]
        
        return cls(
            task_id=task_id,
            evaluations=evaluations,
            final_decision=final_decision
        )


@dataclass
class RunState:
    """Pipeline run state for persistence."""
    run_id: str
    config_hash: str
    total_tasks: int
    completed_tasks: List[str] = field(default_factory=list)
    failed_tasks: List[str] = field(default_factory=list)
    task_results: Dict[str, TaskResult] = field(default_factory=dict)
    total_cost: float = 0.0
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "run_id": self.run_id,
            "config_hash": self.config_hash,
            "total_tasks": self.total_tasks,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "task_results": {
                k: {
                    "task_id": v.task_id,
                    "status": v.status.value,
                    "start_time": v.start_time.isoformat(),
                    "end_time": v.end_time.isoformat() if v.end_time else None,
                    "error_message": v.error_message,
                    "outputs": {ok: str(ov) for ok, ov in v.outputs.items()},
                    "costs": v.costs,
                }
                for k, v in self.task_results.items()
            },
            "total_cost": self.total_cost,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'RunState':
        """Create from dictionary."""
        state = cls(
            run_id=data["run_id"],
            config_hash=data["config_hash"],
            total_tasks=data["total_tasks"],
            completed_tasks=data["completed_tasks"],
            failed_tasks=data["failed_tasks"],
            total_cost=data["total_cost"],
            start_time=datetime.fromisoformat(data["start_time"]),
            end_time=datetime.fromisoformat(data["end_time"]) if data["end_time"] else None,
        )
        
        # Reconstruct task results
        for task_id, result_data in data["task_results"].items():
            state.task_results[task_id] = TaskResult(
                task_id=result_data["task_id"],
                status=TaskStatus(result_data["status"]),
                start_time=datetime.fromisoformat(result_data["start_time"]),
                end_time=datetime.fromisoformat(result_data["end_time"]) if result_data["end_time"] else None,
                error_message=result_data["error_message"],
                outputs={k: Path(v) for k, v in result_data["outputs"].items()},
                costs=result_data["costs"],
            )
        
        return state
    
    def save(self, path: Path) -> None:
        """Save state to JSON file."""
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load(cls, path: Path) -> 'RunState':
        """Load state from JSON file."""
        with open(path, 'r') as f:
            return cls.from_dict(json.load(f))