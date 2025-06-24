"""ElevenLabs TTS provider implementation."""

import asyncio
from pathlib import Path
from typing import Dict, Optional, Tuple
import hashlib
from tenacity import retry, stop_after_attempt, wait_exponential

from ..utils import (
    get_env_var, ensure_dir, get_audio_cache_dir,
    log_info, log_error, log_warning, safe_filename
)
from ..models import Actor


class ElevenLabsProvider:
    """ElevenLabs text-to-speech provider."""
    
    # Estimated cost per character (rough estimate)
    COST_PER_CHARACTER = 0.00015
    
    # Actor to voice ID mapping (example mapping)
    DEFAULT_VOICE_MAPPING = {
        "act_emu01": "21m00Tcm4TlvDq8ikWAM",  # Rachel
        "act_fox02": "AZnzlk1XvdvUeBnXmlld",  # Domi
        "act_lion03": "EXAVITQu4vr4xnSDxMaL",  # Bella
    }
    
    def __init__(self, api_key: Optional[str] = None, voice_mapping: Optional[Dict[str, str]] = None):
        self.api_key = api_key or get_env_var("ELEVENLABS_API_KEY")
        self.voice_mapping = voice_mapping or self.DEFAULT_VOICE_MAPPING
        self.client = None
        self._init_client()
    
    def _init_client(self):
        """Initialize ElevenLabs client."""
        try:
            # Import here to avoid dependency if not using ElevenLabs
            from elevenlabs import AsyncElevenLabs
            self.client = AsyncElevenLabs(api_key=self.api_key)
            log_info("ElevenLabs client initialized")
        except ImportError:
            log_error("ElevenLabs package not installed. Run: pip install elevenlabs")
            raise
        except Exception as e:
            log_error(f"Failed to initialize ElevenLabs client: {e}")
            raise
    
    def _get_voice_id(self, actor_id: str) -> str:
        """Get voice ID for actor."""
        if actor_id not in self.voice_mapping:
            log_warning(f"No voice mapping for {actor_id}, using default")
            return list(self.voice_mapping.values())[0]
        return self.voice_mapping[actor_id]
    
    def _get_cache_path(self, run_id: str, actor_id: str, script_hash: str) -> Path:
        """Get cache path for audio file."""
        cache_dir = ensure_dir(get_audio_cache_dir(run_id))
        filename = f"{actor_id}_{script_hash[:8]}.mp3"
        return cache_dir / filename
    
    def estimate_cost(self, text: str) -> float:
        """Estimate cost for TTS generation."""
        return len(text) * self.COST_PER_CHARACTER
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def generate_speech(
        self,
        text: str,
        actor: Actor,
        run_id: str,
        force_regenerate: bool = False
    ) -> Tuple[Path, float]:
        """
        Generate speech audio for text.
        
        Returns:
            Tuple of (audio_path, cost)
        """
        # Generate cache key
        script_hash = hashlib.md5(text.encode()).hexdigest()
        cache_path = self._get_cache_path(run_id, actor.name, script_hash)
        
        # Check cache
        if cache_path.exists() and not force_regenerate:
            log_info(f"Using cached audio for {actor.name}: {cache_path}")
            return cache_path, 0.0  # No cost for cached
        
        # Generate audio
        log_info(f"Generating audio for {actor.name} ({len(text)} chars)")
        
        try:
            # Use actor's voice_id if available, otherwise use mapping
            voice_id = actor.voice_id or self._get_voice_id(actor.name)
            
            # Generate audio using ElevenLabs
            audio_generator = await self.client.text_to_speech.convert(
                voice_id=voice_id,
                text=text,
                model_id="eleven_monolingual_v1",
                voice_settings={
                    "stability": 0.5,
                    "similarity_boost": 0.75,
                    "style": 0.0,
                    "use_speaker_boost": True
                }
            )
            
            # Save audio to file
            with open(cache_path, 'wb') as f:
                async for chunk in audio_generator:
                    f.write(chunk)
            
            cost = self.estimate_cost(text)
            log_info(f"Generated audio saved to {cache_path} (cost: ${cost:.3f})")
            
            return cache_path, cost
            
        except Exception as e:
            log_error(f"Failed to generate speech for {actor.name}: {e}")
            raise
    
    async def validate_voices(self) -> Dict[str, bool]:
        """Validate that all mapped voices exist."""
        results = {}
        
        try:
            # Get available voices
            voices = await self.client.voices.get_all()
            available_ids = {v.voice_id for v in voices.voices}
            
            # Check each mapping
            for actor_id, voice_id in self.voice_mapping.items():
                results[actor_id] = voice_id in available_ids
                if not results[actor_id]:
                    log_warning(f"Voice {voice_id} not found for actor {actor_id}")
            
            return results
            
        except Exception as e:
            log_error(f"Failed to validate voices: {e}")
            return {actor_id: False for actor_id in self.voice_mapping}


# Placeholder for alternative TTS providers
class MockTTSProvider:
    """Mock TTS provider for testing without API calls."""
    
    async def generate_speech(
        self,
        text: str,
        actor: Actor,
        run_id: str,
        force_regenerate: bool = False
    ) -> Tuple[Path, float]:
        """Generate mock audio file."""
        cache_dir = ensure_dir(get_audio_cache_dir(run_id))
        filename = f"{actor.name}_mock.mp3"
        audio_path = cache_dir / filename
        
        if not audio_path.exists() or force_regenerate:
            # Create empty file as placeholder
            audio_path.touch()
            log_info(f"Created mock audio: {audio_path}")
        
        return audio_path, 0.0