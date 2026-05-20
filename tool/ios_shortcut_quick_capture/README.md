# iOS Shortcut Quick Capture

This is a guide for building an iOS Shortcut that captures text into Navdoc.

Shortcuts are not a stable, reviewable source format, so this directory documents the intended Shortcut behavior instead of storing a `.shortcut` file.

## Shortcut

Name:

```text
Capture to Navdoc
```

iCloud Link:

```text
TODO: Add shared iCloud Shortcut link here.
```

## Behavior

The Shortcut should:

1. Accept text from the Share Sheet when available
2. Ask for text when no Shortcut input is provided
3. Generate a document URL like `inbox/YYYY-MM-DD/HHMMSS`
4. Send `POST /documents`
5. Show a success notification

Do not send `created_at` by default. Let the Navdoc API assign the current time.

## Required User Setup

The user needs a Navdoc API key.

Do not publish or share a Shortcut that contains your own API key.

In the published template, leave the API key placeholder empty or set it to:

```text
YOUR_NAVDOC_API_KEY
```

## Shortcut Actions

Suggested action flow:

1. `Text`
   - Value: `YOUR_NAVDOC_API_KEY`
   - Name this variable `API Key`
2. `If`
   - Condition: `Shortcut Input has any value`
3. Inside the `If` branch:
   - Use `Shortcut Input` as `Content`
4. Inside the `Otherwise` branch:
   - `Ask for Input`
   - Prompt: `Capture text`
   - Type: `Text`
   - Save as `Content`
5. `Current Date`
6. `Format Date`
   - Format: `yyyy-MM-dd`
   - Save as `Date`
7. `Format Date`
   - Format: `HHmmss`
   - Save as `Time`
8. `Text`
   - Value: `inbox/[Date]/[Time]`
   - Save as `Document URL`
9. `Dictionary`
   - `url`: `Document URL`
   - `content`: `Content`
10. `Get Contents of URL`
    - URL: `https://api.navdoc.dev/documents`
    - Method: `POST`
    - Headers:
      - `Authorization`: `Bearer [API Key]`
      - `Content-Type`: `application/json`
    - Request Body: `JSON`
    - JSON payload: dictionary from step 9
11. `Show Notification`
    - Message: `Saved to Navdoc`

## Request Shape

See `request.example.json`.

The Shortcut should send:

```json
{
  "url": "inbox/2026-05-20/153012",
  "content": "Tried Ableton Note. Seems useful for sketching ideas."
}
```

## Notes

This Shortcut is intentionally only a capture surface.

It should not classify, summarize, or triage. Downstream Navdoc agents and pipelines, such as Daily Inbox, can interpret captured documents later.
