from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

from navdoc import NavdocClient


def read_content(args: argparse.Namespace) -> str:
    if args.content:
        return " ".join(args.content).strip()
    if not sys.stdin.isatty():
        return sys.stdin.read().strip()
    raise SystemExit("Provide capture text as arguments or pipe content on stdin.")


def build_url(*, prefix: str, now: datetime) -> str:
    return f"{prefix.rstrip('/')}/{now:%Y-%m-%d}/{now:%H%M%S}"


async def capture(args: argparse.Namespace) -> dict:
    tz = ZoneInfo(args.timezone)
    now = datetime.now(tz)
    content = read_content(args)
    url = args.url or build_url(prefix=args.prefix, now=now)

    payload = {
        "url": url,
        "content": content,
    }
    if args.scope:
        payload["scope"] = args.scope
    if args.created_at:
        payload["created_at"] = args.created_at

    if args.dry_run:
        return {"dry_run": True, **payload}

    client = NavdocClient()
    upload_kwargs = {"url": url}
    if args.scope:
        upload_kwargs["scope"] = args.scope
    if args.created_at:
        upload_kwargs["created_at"] = args.created_at

    doc = await client.upload_document(
        content,
        **upload_kwargs,
    )
    result = {
        "dry_run": False,
        "url": url,
        "document_id": doc.document_id,
        "chunk_count": doc.chunk_count,
    }
    if args.created_at:
        result["created_at"] = args.created_at
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Quickly capture text into navdoc.")
    parser.add_argument("content", nargs="*", help="Text to capture. Reads stdin if omitted.")
    parser.add_argument("--url", help="Document URL. Defaults to inbox/YYYY-MM-DD/HHMMSS.")
    parser.add_argument("--prefix", default="inbox", help="URL prefix used when --url is omitted.")
    parser.add_argument("--scope", help="Optional navdoc scope.")
    parser.add_argument("--created-at", help="Optional ISO 8601 created_at timestamp.")
    parser.add_argument("--timezone", default="Asia/Tokyo", help="IANA timezone for generated URLs and created_at.")
    parser.add_argument("--dry-run", action="store_true", help="Print the payload without uploading.")
    args = parser.parse_args()

    result = asyncio.run(capture(args))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
