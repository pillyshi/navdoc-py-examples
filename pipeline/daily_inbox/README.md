# Daily Inbox Pipeline

Runs two agents in sequence:

1. `config/ask/read/daily_context_extractor.yaml`
2. `pipeline/daily_inbox/config/triage_from_context.yaml`

The first step fetches documents touched on the target date and extracts structured context. The second step triages that JSON into practical buckets without calling tools again.

```bash
uv run python pipeline/daily_inbox/run.py --date 2026-05-19 --language English
```

To inspect the intermediate context:

```bash
uv run python pipeline/daily_inbox/run.py --date 2026-05-19 --language English --include-context
```

See `output.example.json` for a public, fictional example of the final triage output.
