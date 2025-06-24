# Video Mix Pipeline - Project Context

## Overview
This is a focused UGC (User Generated Content) video variation pipeline that generates multiple versions of advertisement videos using different actors and script variations.

## Core Workflow
1. **Input**: One winning video/script + offer ID + actor list
2. **Process**: Generate variants with different actors and minor script tweaks
3. **Output**: Multiple video files with quality evaluations

## Key Components

### Generation Pipeline
- **TTS**: ElevenLabs for voice synthesis
- **Face Sync**: Wav2Lip for lip synchronization
- **Composition**: FFmpeg for final video assembly
- **Evaluation**: Gemini 2.5 Vision ensemble for quality rubric

### Variant Types
- **Type A**: Same script, different actors
- **Type B**: Lightly-tweaked scripts (≤20% wording change), any actor

### Configuration
All parameters defined in YAML config file:
- offer_id, reference video/script
- actor list with IDs
- number of script variants
- provider settings
- cost cap

### CLI Usage
```bash
dicer-ugc run config.yaml
dicer-ugc resume <run_id>
dicer-ugc cost <run_id>
```

## Testing Commands
When making changes, run:
```bash
# Type checking
mypy dicer_ugc/

# Linting
ruff check dicer_ugc/

# Tests
pytest tests/
```

## Project Structure
- `dicer_ugc/` - Main package code
- `tests/` - Test files
- `examples/` - Example configurations
- `output/` - Generated videos (git-ignored)
- `cache/` - Cached face models (git-ignored)

## Important Notes
- Always enforce cost caps to prevent runaway API costs
- Cache intermediate outputs for resume capability
- Use deterministic IDs for reproducibility
- Implement proper error handling with retries
- Track costs per provider (ElevenLabs, Gemini, etc.)

## Development Workflow
1. Make changes to code
2. Run type checking and linting
3. Test with example config
4. Verify cost tracking works correctly
5. Check output organization