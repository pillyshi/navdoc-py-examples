# navdoc Python Examples

Example agents and pipelines built with the [`navdoc`](https://pypi.org/project/navdoc/) Python SDK and CLI.

This repository is organized around two kinds of examples:

- `config/`: standalone agent configs that can be run with `navdoc ask` or `navdoc chat`
- `pipeline/`: Python SDK examples that compose multiple agents into a workflow

## Setup

Install dependencies with `uv`:

```bash
uv sync
```

Set your navdoc API key:

```bash
export NAVDOC_API_KEY=nd_...
```

## Daily Inbox Pipeline

The first pipeline example is `pipeline/daily_inbox`.

It runs two agents in sequence:

1. `config/ask/read/daily_context_extractor.yaml`
2. `pipeline/daily_inbox/config/triage_from_context.yaml`

The first step extracts structured context from documents touched on a target date. The second step triages that context into practical buckets such as actions, memory candidates, interests, review items, and ignored noise.

```bash
uv run python pipeline/daily_inbox/run.py --date 2026-05-19 --language English
```

To include the intermediate context extraction result:

```bash
uv run python pipeline/daily_inbox/run.py --date 2026-05-19 --language English --include-context
```

## Standalone Agent Configs

You can also run standalone configs directly:

```bash
uv run navdoc ask --config config/ask/read/daily_context_extractor.yaml --var date=2026-05-19 --var language=English
```
