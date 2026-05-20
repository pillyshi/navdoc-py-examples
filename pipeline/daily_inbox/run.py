from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml
from navdoc import NavdocClient


ROOT = Path(__file__).resolve().parents[2]
CONTEXT_CONFIG = ROOT / "config" / "ask" / "read" / "daily_context_extractor.yaml"
TRIAGE_CONFIG = Path(__file__).resolve().parent / "config" / "triage_from_context.yaml"


class PipelineError(Exception):
    pass


def load_config(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except OSError as e:
        raise PipelineError(f"could not read config {path}: {e}") from e
    except yaml.YAMLError as e:
        raise PipelineError(f"invalid YAML in config {path}: {e}") from e
    if not isinstance(data, dict):
        raise PipelineError(f"config must be an object: {path}")
    return data


def render_template(template: str, values: dict[str, str]) -> str:
    def replace(match: re.Match[str]) -> str:
        return values.get(match.group(1), match.group(0))

    return re.sub(r"\{\{(\w+)\}\}", replace, template)


def parse_json_answer(answer: str, *, step: str) -> Any:
    text = answer.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        preview = text[:500]
        raise PipelineError(
            f"{step} returned invalid JSON at line {e.lineno}, column {e.colno}: {e.msg}\n"
            f"Response preview:\n{preview}"
        ) from e


async def ask_with_config(
    client: NavdocClient,
    config: dict[str, Any],
    values: dict[str, str],
    *,
    step: str,
    timezone: str,
) -> Any:
    system_prompt = render_template(config.get("system_prompt", ""), values)
    user_prompt = render_template(config.get("user_prompt", ""), values)
    try:
        response = await client.ask_server(
            user_prompt,
            timezone=timezone,
            system_prompt=system_prompt,
            tools=config.get("tools"),
            output_format=config.get("output_format", "text"),
            temperature=config.get("temperature"),
        )
    except Exception as e:
        raise PipelineError(f"{step} failed: {e}") from e
    return parse_json_answer(response.answer, step=step)


async def run_pipeline(args: argparse.Namespace) -> dict[str, Any]:
    client = NavdocClient()

    context_config = load_config(CONTEXT_CONFIG)
    triage_config = load_config(TRIAGE_CONFIG)

    context = await ask_with_config(
        client,
        context_config,
        {"date": args.date, "language": args.language},
        step="daily context extractor",
        timezone=args.timezone,
    )
    triage = await ask_with_config(
        client,
        triage_config,
        {
            "language": args.language,
            "context_json": json.dumps(context, ensure_ascii=False, indent=2),
        },
        step="triage from context",
        timezone=args.timezone,
    )

    if args.include_context:
        return {"context": context, "triage": triage}
    return triage


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the daily inbox pipeline.")
    parser.add_argument("--date", default="today", help="Date in YYYY-MM-DD format, or 'today'.")
    parser.add_argument("--language", default="English", help="Response language.")
    parser.add_argument("--timezone", default="Asia/Tokyo", help="IANA timezone.")
    parser.add_argument(
        "--include-context",
        action="store_true",
        help="Print both the Daily Context output and final triage output.",
    )
    args = parser.parse_args()

    try:
        result = asyncio.run(run_pipeline(args))
    except PipelineError as e:
        print(f"Error: {e}", file=sys.stderr)
        raise SystemExit(1) from e
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        raise SystemExit(130)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
