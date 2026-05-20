# Interest Radar Pipeline

Scans documents from a date range, extracts interest signals, then clusters and ranks them into a radar view.

Runs two agents in sequence:

1. `config/extract_interests.yaml` — reads all documents in the range and extracts raw interest signals with source evidence
2. `config/rank_interests.yaml` — clusters related topics and scores each by frequency, recency, and intensity

## Usage

Scan the last 7 days (default):

```bash
uv run python pipeline/interest_radar/run.py
```

Scan a specific number of days:

```bash
uv run python pipeline/interest_radar/run.py --days 14
```

Scan a specific date range:

```bash
uv run python pipeline/interest_radar/run.py --start 2026-05-01 --end 2026-05-20
```

To inspect the raw extracted interests before ranking:

```bash
uv run python pipeline/interest_radar/run.py --days 14 --include-extracted
```

See `output.example.json` for a public, fictional example of the final radar output.
