"""Configuration management with Pydantic validation."""

from pathlib import Path
from typing import List, Literal, Optional, Union, Dict
from pydantic import BaseModel, Field, field_validator, ConfigDict
import yaml

from .models import Actor, OfferMetadata


class ReferenceConfig(BaseModel):
    """Reference video and script configuration."""
    
    video: Path = Field(description="Path to reference video file")
    script: Union[Path, str] = Field(description="Path to script file or inline script text")
    
    @field_validator('video')
    def validate_video_path(cls, v: Path) -> Path:
        if not v.exists():
            raise ValueError(f"Reference video not found: {v}")
        if v.suffix.lower() not in ['.mp4', '.mov', '.avi']:
            raise ValueError(f"Invalid video format: {v.suffix}")
        return v
    
    @field_validator('script')
    def validate_script(cls, v: Union[Path, str]) -> Union[Path, str]:
        if isinstance(v, Path) and not v.exists():
            raise ValueError(f"Script file not found: {v}")
        return v


class VariantConfig(BaseModel):
    """Variant generation configuration."""
    
    identical_script: bool = Field(True, description="Generate identical script variants")
    minor_script_variants: int = Field(
        3, 
        description="Number of minor script variants per actor",
        ge=0,
        le=10
    )


class RubricConfig(BaseModel):
    """Rubric evaluation configuration."""
    
    ensemble: int = Field(
        3,
        description="Number of models for ensemble evaluation (must be odd)",
        ge=1,
        le=7
    )
    temperature: float = Field(
        0.1,
        description="Temperature for LLM evaluation",
        ge=0.0,
        le=1.0
    )
    
    @field_validator('ensemble')
    def validate_ensemble(cls, v: int) -> int:
        if v % 2 == 0:
            raise ValueError("Ensemble size must be odd for majority voting")
        return v


class ProvidersConfig(BaseModel):
    """External provider configuration."""
    
    tts: Literal["eleven"] = Field("eleven", description="TTS provider")
    face_sync: Literal["wav2lip"] = Field("wav2lip", description="Face sync provider")


class VideoPipelineConfig(BaseModel):
    """Video pipeline configuration."""
    
    ugc_only: bool = Field(False, description="Skip B-roll and captions")
    add_captions: bool = Field(True, description="Add captions to final video")
    b_roll_style: Optional[str] = Field(None, description="B-roll style/theme")


class PipelineConfig(BaseModel):
    """Main pipeline configuration."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )
    
    offer_id: str = Field(description="Unique offer identifier")
    offer_metadata: Optional[OfferMetadata] = Field(None, description="Product/offer information")
    reference: ReferenceConfig
    actors: List[Union[str, Dict, Actor]] = Field(
        description="List of actors (names, dicts, or Actor objects)",
        min_length=1,
        max_length=20
    )
    variants: VariantConfig = Field(default_factory=VariantConfig)
    rubric: RubricConfig = Field(default_factory=RubricConfig)
    providers: ProvidersConfig = Field(default_factory=ProvidersConfig)
    video_pipeline: VideoPipelineConfig = Field(default_factory=VideoPipelineConfig)
    cost_cap: float = Field(
        30.0,
        description="Maximum cost in USD",
        gt=0,
        le=1000
    )
    
    @field_validator('actors')
    def validate_actors(cls, v: List[Union[str, Dict, Actor]]) -> List[Actor]:
        """Convert various actor formats to Actor objects."""
        actors = []
        names_seen = set()
        
        for item in v:
            if isinstance(item, Actor):
                actor = item
            elif isinstance(item, dict):
                actor = Actor(**item)
            elif isinstance(item, str):
                # Legacy format - just actor name
                actor = Actor(name=item, scene_id="")
            else:
                raise ValueError(f"Invalid actor format: {type(item)}")
            
            if actor.name in names_seen:
                raise ValueError(f"Duplicate actor name: {actor.name}")
            names_seen.add(actor.name)
            actors.append(actor)
        
        return actors
    
    @property
    def total_videos(self) -> int:
        """Calculate total number of videos to generate."""
        return len(self.actors) * (1 + self.variants.minor_script_variants)
    
    @property
    def estimated_cost(self) -> tuple[float, float]:
        """Estimate cost range (min, max) in USD."""
        # Rough estimates per video
        tts_cost_per_video = 0.15  # ElevenLabs
        rubric_cost_per_video = 0.02 * self.rubric.ensemble  # Gemini
        
        cost_per_video = tts_cost_per_video + rubric_cost_per_video
        total_cost = self.total_videos * cost_per_video
        
        # Return range with 20% margin
        return (total_cost * 0.8, total_cost * 1.2)


def load_config(config_path: Path) -> PipelineConfig:
    """Load and validate configuration from YAML file."""
    with open(config_path, 'r') as f:
        data = yaml.safe_load(f)
    
    # Convert script path string to Path if needed
    if 'reference' in data and 'script' in data['reference']:
        script_value = data['reference']['script']
        if isinstance(script_value, str) and (
            script_value.startswith('/') or 
            script_value.startswith('./') or
            script_value.endswith('.txt')
        ):
            data['reference']['script'] = Path(script_value)
    
    # Convert video path string to Path
    if 'reference' in data and 'video' in data['reference']:
        data['reference']['video'] = Path(data['reference']['video'])
    
    # Convert offer_metadata if present
    if 'offer_metadata' in data and isinstance(data['offer_metadata'], dict):
        data['offer_metadata'] = OfferMetadata(**data['offer_metadata'])
    
    return PipelineConfig(**data)


def save_example_config(output_path: Path) -> None:
    """Save an example configuration file."""
    example = {
        "offer_id": "ccw713",
        "reference": {
            "video": "/data/ref/ccw713/winner.mp4",
            "script": "/data/ref/ccw713/winner.txt"
        },
        "actors": [
            {
                "name": "olivia",
                "scene_id": "9bd1e9ed-5747-4052-96fe-1b6862e6dada"
            },
            {
                "name": "janet",
                "scene_id": "5513cdb5-c6c7-483e-8b94-67f6a42f1747"
            },
            {
                "name": "ernest",
                "scene_id": "6fb4c27f-cf6a-41af-a292-9439b0628187"
            }
        ],
        "variants": {
            "identical_script": True,
            "minor_script_variants": 3
        },
        "rubric": {
            "ensemble": 3,
            "temperature": 0.1
        },
        "providers": {
            "tts": "eleven",
            "face_sync": "wav2lip"
        },
        "video_pipeline": {
            "ugc_only": False,
            "add_captions": True,
            "b_roll_style": "product_demo"
        },
        "cost_cap": 30.0
    }
    
    with open(output_path, 'w') as f:
        yaml.dump(example, f, default_flow_style=False, sort_keys=False)