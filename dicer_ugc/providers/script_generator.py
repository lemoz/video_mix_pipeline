"""Script generation and variation using LLMs."""

import json
from typing import List, Optional, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential

from ..models import Actor, OfferMetadata
from ..utils import get_env_var, log_info, log_error, log_warning
from ..cost_tracker import CostTracker, Provider


class ScriptGenerator:
    """Generate script variations using LLMs."""
    
    def __init__(self, api_key: Optional[str] = None, cost_tracker: Optional[CostTracker] = None):
        self.api_key = api_key or get_env_var("GEMINI_API_KEY")
        self.cost_tracker = cost_tracker
        self.client = None
        self._init_client()
    
    def _init_client(self):
        """Initialize Gemini client."""
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.client = genai.GenerativeModel('gemini-1.5-flash')
            log_info("Gemini client initialized for script generation")
        except ImportError:
            log_error("Google Generative AI package not installed. Run: pip install google-generativeai")
            raise
        except Exception as e:
            log_error(f"Failed to initialize Gemini client: {e}")
            raise
    
    def _build_variation_prompt(
        self,
        base_script: str,
        actor: Actor,
        offer_metadata: Optional[OfferMetadata] = None,
        variation_num: int = 1
    ) -> str:
        """Build prompt for script variation."""
        prompt = f"""Rewrite this advertisement script with minor variations while maintaining the core message.

ORIGINAL SCRIPT:
{base_script}

CONSTRAINTS:
1. Keep the same overall structure and flow
2. Maintain all key features and benefits mentioned
3. Keep the same call-to-action intent
4. Change approximately 15-20% of the wording
5. Preserve the conversational, authentic tone
6. Keep roughly the same length (within 10 words)
7. Ensure full compliance with advertising standards

VARIATION GUIDELINES:
- Change the opening hook but keep it personal
- Vary specific phrases and expressions
- Use different comparisons or examples
- Adjust emotional reactions (surprised → amazed, shocked → impressed)
- Rephrase benefits in slightly different ways
- Keep the core selling points intact

"""
        
        if offer_metadata:
            prompt += f"""
BRAND CONTEXT:
- Product: {offer_metadata.name}
- Key Features: {', '.join(offer_metadata.key_features[:3])}
- Brand Elements: {', '.join(offer_metadata.brand_elements[:2])}
- Must Avoid: {', '.join(offer_metadata.avoid_showing[:2])}

"""
        
        prompt += f"""
ACTOR CONTEXT:
- Speaker: {actor.name}
- Style: {actor.style or 'conversational'}
- This is variation #{variation_num} for this actor

OUTPUT FORMAT:
Return ONLY the rewritten script text. Do not include any explanations, metadata, or formatting.
Do not use quotation marks around the script.
"""
        
        return prompt
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def generate_variation(
        self,
        base_script: str,
        actor: Actor,
        offer_metadata: Optional[OfferMetadata] = None,
        variation_num: int = 1,
        temperature: float = 0.7
    ) -> tuple[str, float]:
        """
        Generate a script variation.
        
        Returns:
            Tuple of (varied_script, cost)
        """
        prompt = self._build_variation_prompt(base_script, actor, offer_metadata, variation_num)
        
        try:
            # Generate with Gemini
            response = await self.client.generate_content_async(
                prompt,
                generation_config={
                    "temperature": temperature,
                    "max_output_tokens": 500,
                }
            )
            
            # Extract text
            varied_script = response.text.strip()
            
            # Track cost (approximate)
            input_tokens = len(prompt.split()) * 1.3  # Rough estimate
            output_tokens = len(varied_script.split()) * 1.3
            total_tokens = int(input_tokens + output_tokens)
            
            cost = 0.0
            if self.cost_tracker:
                cost = self.cost_tracker.track_cost(
                    provider=Provider.GEMINI,
                    operation="script_generation",
                    units=total_tokens,
                    unit_cost=0.00001,  # $0.01 per 1K tokens
                    metadata={"actor": actor.name, "variation": variation_num}
                )
            
            # Validate variation
            word_count_diff = abs(len(varied_script.split()) - len(base_script.split()))
            if word_count_diff > 20:
                log_warning(f"Variation word count differs by {word_count_diff} words")
            
            log_info(f"Generated script variation {variation_num} for {actor.name} (cost: ${cost:.3f})")
            return varied_script, cost
            
        except Exception as e:
            log_error(f"Failed to generate script variation: {e}")
            raise
    
    async def generate_all_variations(
        self,
        base_script: str,
        actor: Actor,
        num_variations: int,
        offer_metadata: Optional[OfferMetadata] = None,
        temperature: float = 0.7
    ) -> List[tuple[str, float]]:
        """Generate multiple script variations for an actor."""
        variations = []
        
        for i in range(1, num_variations + 1):
            try:
                script, cost = await self.generate_variation(
                    base_script,
                    actor,
                    offer_metadata,
                    variation_num=i,
                    temperature=temperature
                )
                variations.append((script, cost))
            except Exception as e:
                log_error(f"Failed to generate variation {i} for {actor.name}: {e}")
                # Continue with other variations
        
        return variations


class MockScriptGenerator:
    """Mock script generator for testing."""
    
    async def generate_variation(
        self,
        base_script: str,
        actor: Actor,
        offer_metadata: Optional[OfferMetadata] = None,
        variation_num: int = 1,
        temperature: float = 0.7
    ) -> tuple[str, float]:
        """Generate mock variation."""
        # Simple variation: prepend actor name and variation number
        varied_script = f"[{actor.name} - Variation {variation_num}] {base_script}"
        return varied_script, 0.0
    
    async def generate_all_variations(
        self,
        base_script: str,
        actor: Actor,
        num_variations: int,
        offer_metadata: Optional[OfferMetadata] = None,
        temperature: float = 0.7
    ) -> List[tuple[str, float]]:
        """Generate mock variations."""
        variations = []
        for i in range(1, num_variations + 1):
            script, cost = await self.generate_variation(
                base_script, actor, offer_metadata, i, temperature
            )
            variations.append((script, cost))
        return variations