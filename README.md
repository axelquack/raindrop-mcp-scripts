# Raindrop.io Scripts

A small collection of Python scripts for bulk managing a [Raindrop.io](https://raindrop.io) bookmark library via the Raindrop MCP API. No external dependencies beyond Python 3 and `curl`.

> **Raindrop Pro required.** The MCP API and AI features (`find_misplaced_bookmarks`, `find_mistagged_bookmarks`, `fetch_bookmark_content`) are only available on a [Raindrop Pro](https://raindrop.io/pro) subscription.

## Scripts

| Script | Purpose |
|---|---|
| `raindrop_cleanup.py` | Interactive AI-powered library maintenance |
| `raindrop_importer.py` | Import bookmarks from `.webloc` files or Markdown |
| `raindrop_utils.py` | Shared utility library used by both scripts |

---

## Setup

**1. Get your Raindrop API token**

Go to [app.raindrop.io](https://app.raindrop.io) → Settings → Integrations → **For Developers** → copy the **Test token**.

**2. Configure your token**

```bash
cp .env.example .env
```

Edit `.env` and paste your token:

```
RAINDROP_TOKEN=your_test_token_here
```

**3. Requirements**

- Python 3.10+
- `curl` (pre-installed on macOS and most Linux systems)

No `pip install` needed.

---

## raindrop_importer.py

Imports bookmarks from a folder of Safari `.webloc` files or a Markdown file containing URLs. All bookmarks land in **Unsorted** with tag `imported`. Run `raindrop_cleanup.py` afterwards to sort and tag them.

```bash
python3 raindrop_importer.py
```

You will be prompted to choose:

1. **Markdown file** — parses `[title](url)` links and bare URLs; ignores all other lines (headings, paragraphs, code blocks)
2. **Folder of .webloc files** — extracts URLs from Safari bookmark files; deletes each `.webloc` after successful upload

### Markdown format

The importer handles two URL formats per line:

```markdown
[My Link Title](https://example.com)   → title: "My Link Title"
https://example.com                    → title: "https://example.com"
```

Any line without a URL is silently ignored, so you can keep notes, headings, or other text in the same file.

---

## raindrop_cleanup.py

An interactive maintenance agent that walks you through 4 steps, asking for approval on each suggestion before applying any change.

```bash
python3 raindrop_cleanup.py
```

### Steps

| Step | What it does |
|---|---|
| 1 — Theme Discovery | Shows the most common topics across your library |
| 2 — Misplaced Bookmarks | AI flags bookmarks that seem to be in the wrong collection |
| 3 — Inconsistent Tags | AI flags bookmarks whose tags don't match their content |
| 4 — Broken Links | Lists potentially broken links for manual review (no auto-delete) |

### Controls

| Key | Action |
|---|---|
| `y` | Accept / apply suggestion |
| `e` | Edit suggestion before applying |
| `m` | Move to a different collection (numbered chooser) |
| `f` | Flag with `review` tag, handle later in Raindrop |
| `n` | Skip this item |
| `s` | Skip the rest of the current step |
| `q` | Quit |

### Notes

- **Step 2** fetches collections live each run — no hardcoded IDs. The `m` chooser shows a numbered hierarchical list with parent/child indentation.
- **Step 3** uses `fetch_bookmark_content` to suggest better tags. If the API returns no suggestion, it falls back to manual editing with the current tags pre-filled.
- **Step 4** is display-only — no deletions. It automatically filters out false positives (YouTube, GitHub, Instagram, Imgur, etc.) that block automated link checkers. Always verify manually before deleting anything in Raindrop.
- **Tag replacement** (`e` / edit) uses the Raindrop REST API directly since the MCP `update_bookmarks` tool only supports `add_tags`, not full replacement.

---

## raindrop_utils.py

Shared utility library. Import it in your own scripts:

```python
import sys
sys.path.insert(0, "/path/to/raindrop-scripts")
import raindrop_utils as rd

# List all collections
for c in rd.list_collections():
    print(c["collection_id"], c["title"])

# Fetch all bookmarks from a collection
items = rd.fetch_all_from_collection(22803193)

# Batch update — move + add tags + note in one call
rd.update_bookmarks([
    {"bookmark_ids": [123456], "update": {
        "collection_id": 8995033,
        "add_tags": ["self-hosting"],
        "note": "Brief description of this link"
    }}
])

# Full tag replacement (routes via REST API automatically)
rd.update_bookmarks([
    {"bookmark_ids": [123456], "update": {
        "tags": ["new", "tags", "only"]
    }}
])
```

### Key functions

| Function | Description |
|---|---|
| `mcp_call(tool, args)` | Raw MCP tool call |
| `get_text(response)` | Extract text from MCP response |
| `rest_get(path, params)` | Direct REST API GET |
| `rest_put(path, body)` | Direct REST API PUT |
| `list_collections()` | All collections sorted by count |
| `collections_by_name()` | `{name.lower(): id}` map, fetched live |
| `fetch_all_from_collection(id)` | Paginated fetch via REST (more reliable than MCP for large collections) |
| `find_untagged(limit, page)` | Bookmarks with no tags |
| `update_bookmarks(updates)` | Batch update, auto-routes REST vs MCP |

---

## Known Limitations

These are gaps between what the Raindrop app/web UI offers and what is available through the API.

| Limitation | Detail |
|---|---|
| **No tag suggestions in CLI** | `find_mistagged_bookmarks` only returns the flagged bookmarks — it does not return suggested replacement tags. The Raindrop app and web UI show tag suggestions visually, but this data is not exposed via the MCP or REST API. In the CLI you have to type corrections manually. ([#22](https://github.com/raindropio/developer-site/issues/22)) |
| **No collection icons via API** | Collection emoji/icons can only be set in the Raindrop UI (right-click → Edit). Neither the MCP nor the REST API accept an icon or emoji field. ([#26](https://github.com/raindropio/developer-site/issues/26)) |
| **Broken link detection unreliable** | Many sites (YouTube, GitHub, Instagram, Twitter, Imgur, etc.) block automated HTTP checkers and get incorrectly flagged as broken. The cleanup script filters the most common false-positive domains, but the list is not exhaustive. Always verify manually before deleting. |
| **`find_bookmarks` unreliable for specific collections** | The MCP `find_bookmarks` tool sometimes returns `"Unknown error"` when filtering by a specific `collection_id`. Likely caused by concurrent read/write on the same collection. The scripts work around this by using the direct REST API (`/raindrops/{id}`) for collection-scoped fetches. ([#25](https://github.com/raindropio/developer-site/issues/25)) |
| **`update_bookmarks` combined tag ops fail** | The MCP `update_bookmarks` tool supports `add_tags` and `remove_tags` as standalone operations, but using both in the same op returns `"Unknown error"` (server-side path conflict). Full tag replacement requires a direct REST `PUT /raindrop/{id}`. The `update_bookmarks()` function in `raindrop_utils.py` handles all three cases automatically: standalone ops go via MCP, combined `remove_tags` + `add_tags` is auto-split into two sequential MCP calls, and `tags` (full replacement) goes via REST. ([#24](https://github.com/raindropio/developer-site/issues/24)) |
| **`fetch_bookmark_content` returns no tags** | Despite the name suggesting rich content analysis, the tool currently returns no tag suggestions through the API — only the raw page content or nothing at all. |
| **`find_misplaced_bookmarks` ignores Unsorted** | Passing `collection_ids: [-1]` (Unsorted) returns no suggestions. By design — the tool evaluates whether a bookmark belongs in its current named collection; Unsorted has no semantic identity to evaluate against. Use `find_bookmarks` with `collection_ids: [-1]` instead and let the LLM decide placement. ([#23](https://github.com/raindropio/developer-site/issues/23)) |

---

## API Notes

- The Raindrop MCP endpoint is **stateless** — no `initialize` handshake or session ID needed.
- `find_bookmarks` with a specific `collection_ids` value sometimes returns `"Unknown error"` from the MCP. Use `fetch_all_from_collection()` (REST API) instead.
- `update_bookmarks` via MCP supports `add_tags`, `remove_tags`, `collection_id`, and `note`. Combining `remove_tags` + `add_tags` in one op fails — `update_bookmarks()` auto-splits these. Full tag replacement via `tags` routes to REST automatically.
- Collection icons/emoji are **not settable via the API** — UI only.
- Rate limit: 120 requests/minute.

---

## .gitignore

Make sure `.env` is in your `.gitignore`:

```
.env
```
