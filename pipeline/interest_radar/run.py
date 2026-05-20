from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import yaml
from navdoc import NavdocClient


PIPELINE_DIR = Path(__file__).resolve().parent
EXTRACT_CONFIG = PIPELINE_DIR / "config" / "extract_interests.yaml"
RANK_CONFIG = PIPELINE_DIR / "config" / "rank_interests.yaml"


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
    print(f"[{step}] submitting job...", file=sys.stderr)
    try:
        response = await client.ask_server(
            user_prompt,
            timezone=timezone,
            system_prompt=system_prompt,
            tools=config.get("tools"),
            output_format=config.get("output_format", "text"),
            temperature=config.get("temperature"),
            poll_timeout=config.get("poll_timeout", 300.0),
        )
    except Exception as e:
        raise PipelineError(f"{step} failed: {e}") from e
    print(f"[{step}] done.", file=sys.stderr)
    return parse_json_answer(response.answer, step=step)


def resolve_date_range(args: argparse.Namespace) -> tuple[str, str]:
    today = date.today()
    if args.start:
        date_from = args.start
        date_to = args.end or today.isoformat()
    else:
        date_from = (today - timedelta(days=args.days - 1)).isoformat()
        date_to = today.isoformat()
    return date_from, date_to


async def run_pipeline(args: argparse.Namespace) -> dict[str, Any]:
    client = NavdocClient()
    date_from, date_to = resolve_date_range(args)

    extract_config = load_config(EXTRACT_CONFIG)
    rank_config = load_config(RANK_CONFIG)

    # Process one day at a time to stay within server response time limits.
    all_interests: list[Any] = []
    seen_sources: set[str] = set()
    all_sources: list[str] = []

    current = date.fromisoformat(date_from)
    end = date.fromisoformat(date_to)
    while current <= end:
        d = current.isoformat()
        day_result = await ask_with_config(
            client,
            extract_config,
            {"date_from": d, "date_to": d, "language": args.language},
            step=f"extract interests ({d})",
            timezone=args.timezone,
        )
        n = len(day_result.get("interests", []))
        print(f"  -> {n} interest(s) found.", file=sys.stderr)
        all_interests.extend(day_result.get("interests", []))
        for src in day_result.get("sources", []):
            if src not in seen_sources:
                seen_sources.add(src)
                all_sources.append(src)
        current += timedelta(days=1)

    combined = {
        "date_range": {"from": date_from, "to": date_to},
        "sources": all_sources,
        "interests": all_interests,
    }

    if args.include_extracted:
        print(json.dumps(combined, ensure_ascii=False, indent=2), flush=True)
        print("---", flush=True)

    if not all_interests:
        return {
            "date_range": {"from": date_from, "to": date_to},
            "radar": [],
            "clusters": [],
            "summary": "No interests found in the specified period.",
        }

    interests_json = json.dumps(combined, ensure_ascii=False, indent=2)
    print(f"Ranking {len(all_interests)} interest(s) ({len(interests_json)} chars)...", file=sys.stderr)
    ranked = await ask_with_config(
        client,
        rank_config,
        {
            "language": args.language,
            "interests_json": interests_json,
        },
        step="rank interests",
        timezone=args.timezone,
    )
    return ranked


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Interest Radar pipeline.")
    range_group = parser.add_mutually_exclusive_group()
    range_group.add_argument(
        "--days",
        type=int,
        default=7,
        metavar="N",
        help="Scan the last N days (default: 7).",
    )
    range_group.add_argument(
        "--start",
        metavar="YYYY-MM-DD",
        help="Start date of the range.",
    )
    parser.add_argument(
        "--end",
        metavar="YYYY-MM-DD",
        help="End date of the range (default: today). Only used with --start.",
    )
    parser.add_argument("--language", default="English", help="Response language.")
    parser.add_argument("--timezone", default="Asia/Tokyo", help="IANA timezone.")
    parser.add_argument(
        "--include-extracted",
        action="store_true",
        help="Print the raw extracted interests JSON before the final radar output.",
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
