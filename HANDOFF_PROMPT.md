# UGC Video Variation Pipeline - Extending Existing Codebase

## Context
I need your help extending an existing video generation codebase to implement a focused UGC (User Generated Content) variation pipeline. We've already done significant planning and prototyping, and now need to adapt that work to an existing repository.

## Project Goal
Build a pipeline that takes:
- One winning video/script reference
- A fixed list of actors (with scene IDs)
- Generates variants: same script with different actors + lightly-tweaked scripts (≤20% change)

## Key Requirements from Planning Phase

### 1. Core Workflow
```
One offer → one winning video + script →
- Variant A: same script, different actors  
- Variant B: minor script variants, any actor from list
```

### 2. Real Production Data Structure
We discovered the actual system uses:
- **Actor Scene IDs**: UUID-based (e.g., olivia: "9bd1e9ed-5747-4052-96fe-1b6862e6dada")
- **Multi-stage videos**: UGC base → B-roll integration → Captioned final
- **Rich metadata**: Offer details, brand guidelines, competitor info

### 3. Critical Components Identified
1. **Variant Matrix Builder**: Generates deterministic task list
2. **Script Generator**: LLM-based variations maintaining brand voice
3. **Cost Tracker**: Hard cap enforcement, per-provider tracking
4. **Video Pipeline**: UGC → B-roll → Captions flow
5. **Resume Capability**: State persistence for interrupted runs

### 4. Example Data
OTTO Auto Insurance scripts show pattern:
- Personal opening hook
- Problem statement  
- OTTO solution discovery
- Benefits (free quotes, multiple providers, minutes)
- Satisfaction + CTA
- ~100-150 words, conversational tone

## Your Tasks

### Phase 1: Repository Analysis
1. Clone and explore the existing repository structure
2. Identify existing video generation components
3. Find actor/scene management systems
4. Locate TTS, video composition, or face sync code
5. Understand the current config/workflow system

### Phase 2: Gap Analysis
Compare what exists vs. what we need:
- Variant generation logic
- Script modification capabilities  
- Cost tracking/caps
- Batch processing with parallelism
- Actor scene ID integration

### Phase 3: Integration Plan
Create a plan that:
- Leverages existing code maximally
- Adds our variant matrix concept
- Integrates real actor scene IDs
- Implements script variations
- Adds cost control

### Phase 4: Implementation
Extend the codebase while:
- Maintaining existing functionality
- Following repo's patterns/style
- Adding our new capabilities
- Creating example configs

## Key Decisions to Preserve
1. Use Pydantic for config validation
2. Async processing with semaphore for parallelism  
3. Deterministic task IDs for resume capability
4. Cost tracking at operation level
5. Separate providers for modularity

## Questions to Answer Early
1. Does the repo already have actor/scene management?
2. Is there existing TTS integration (ElevenLabs)?
3. How does it handle video composition?
4. What's the current config format?
5. Is there batch processing infrastructure?

## Success Criteria
- Can generate N actors × M script variants
- Enforces cost caps
- Supports resume after interruption  
- Produces videos matching production examples
- Works with real actor scene IDs

## Reference Implementation Structure
We prototyped the following structure which should guide the integration:

```python
# Core models
@dataclass
class Actor:
    name: str
    scene_id: str
    voice_id: Optional[str]

@dataclass
class VariantTask:
    task_id: str
    actor: Actor
    variant_type: VariantType
    variant_num: int
    script_text: str
    offer_metadata: Optional[OfferMetadata]

# Key components
- VariantMatrixBuilder: Builds deterministic task matrix
- CostTracker: Enforces caps, tracks per-provider costs  
- ScriptGenerator: LLM-based script variations
- VideoComposer: Orchestrates UGC→B-roll→Captions
```

## Additional Context Files
- `/examples/otto_auto_insurance.yaml` - Full example configuration
- `/examples/otto_scripts.txt` - Real script examples and variations
- `/dicer_ugc/actor_mapping.py` - Complete actor scene ID mappings

Please start by thoroughly analyzing the repository structure and then create an integration plan before making any changes. Focus on understanding before implementing.