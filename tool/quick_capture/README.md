# Quick Capture

Minimal write-side example for navdoc.

Quick Capture creates one navdoc document per capture using the Python SDK. It is intentionally simple: it only calls `NavdocClient.upload_document()`, which maps to `POST /documents`.

## Usage

Capture a short note:

```bash
uv run python tool/quick_capture/capture.py "Tried Ableton Note. Seems useful for sketching ideas."
```

Capture from stdin:

```bash
echo "Read a useful note about local recycling." | uv run python tool/quick_capture/capture.py
```

Provide your own document URL:

```bash
uv run python tool/quick_capture/capture.py \
  --url inbox/2026-05-20/ableton-note \
  "This app looks fun. I want to try it."
```

Preview without writing:

```bash
uv run python tool/quick_capture/capture.py --dry-run "Draft capture"
```

## URL Format

If `--url` is omitted, Quick Capture generates a URL like:

```text
inbox/YYYY-MM-DD/HHMMSS
```

This works well with read-side examples such as `pipeline/daily_inbox`, because each capture becomes an individual document that can be discovered later by `list_documents_by_date`.
