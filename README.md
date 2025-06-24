# Video Mix Pipeline

A focused UGC (User Generated Content) video variation pipeline that generates multiple versions of advertisement videos using different actors and script variations.

## Features

- Generate video variants with different actors (same script)
- Create minor script variations (≤20% wording change)
- Automated TTS with ElevenLabs
- Face synchronization with Wav2Lip
- Quality evaluation using Gemini 2.5 Vision
- Cost tracking and caps
- Resume capability for interrupted runs

## Installation

```bash
pip install -e .
```

## Quick Start

1. Create a configuration file:

```yaml
offer_id: ccw713
reference:
  video: /data/ref/ccw713/winner.mp4
  script: /data/ref/ccw713/winner.txt
actors:
  - act_emu01
  - act_fox02
  - act_lion03
variants:
  identical_script: true
  minor_script_variants: 3
rubric:
  ensemble: 3
  temperature: 0.1
providers:
  tts: eleven
  face_sync: wav2lip
cost_cap: 30
```

2. Run the pipeline:

```bash
dicer-ugc run config.yaml
```

3. Check results:

```bash
dicer-ugc cost <run_id>
```

## Output Structure

```
/output/<run_id>/
  videos/              # Generated MP4 files
  manifest.json        # Actor + variant mapping
  rubric.jsonl         # Quality evaluations
  accepted.list        # Videos that passed rubric
  review.list          # Videos needing manual review
  rejected.list        # Videos that failed rubric
  cost_report.json     # Detailed cost breakdown
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Type checking
mypy dicer_ugc/

# Linting
ruff check dicer_ugc/
```

## License

MIT