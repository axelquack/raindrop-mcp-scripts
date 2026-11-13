# Bugfixes

Durable bug writeups. One heading per bug: `BF-NNN`. Keep the number. Do not reuse it.

These are lasting limits of the Raindrop API and of automated link checks. The script guide in `README.md` states the same limits. There was no earlier `BUGFIXES.md` to merge.

## BF-001 — No tag suggestions in the CLI

- Status: open
- Date: 2026-04-06
- Symptom: `find_mistagged_bookmarks` returns the flagged bookmarks and does not return suggested replacement tags. The app and the web UI show suggestions. The CLI user types the correction.
- Cause: Suggested tags are not exposed through the MCP or REST API. Upstream developer-site issue 22.
- Policy: Type corrections manually. Do not invent suggestions the API did not return.

## BF-002 — Collection icons are UI-only

- Status: open
- Date: 2026-04-06
- Symptom: A script cannot set a collection emoji or icon.
- Cause: Neither the MCP nor the REST API accepts an icon or emoji field. Upstream developer-site issue 26.
- Policy: Set icons in the Raindrop UI.

## BF-003 — Broken-link checks flag sites that block checkers

- Status: open
- Date: 2026-04-06
- Symptom: YouTube, GitHub, Instagram, and similar sites are reported broken because they block automated HTTP checks.
- Cause: Those sites refuse the checker. The cleanup script skips a fixed domain list. The list is not exhaustive.
- Policy: Step 4 is display-only. Verify in the Raindrop UI before deleting anything. Do not auto-delete.

## BF-004 — `find_bookmarks` fails for one collection

- Status: open
- Date: 2026-04-06
- Symptom: MCP `find_bookmarks` sometimes returns an unknown error when filtered to one `collection_id`.
- Cause: Likely concurrent read and write on the same collection. Upstream developer-site issue 25.
- Policy: Use `fetch_all_from_collection` (REST `/raindrops/{id}`) for a collection-scoped fetch.

## BF-005 — Combined tag add and remove fails on MCP

- Status: open
- Date: 2026-04-06
- Symptom: One MCP `update_bookmarks` call that both removes and adds tags returns an unknown error. Full replacement is not an MCP operation.
- Cause: Server-side path conflict when `remove_tags` and `add_tags` share one operation. Upstream developer-site issue 24.
- Policy: `update_bookmarks()` in `raindrop_utils.py` sends standalone ops via MCP, splits a combined remove-plus-add into two MCP calls, and sends a full `tags` replacement via REST `PUT /raindrop/{id}`.

## BF-006 — `fetch_bookmark_content` returns no tags

- Status: open
- Date: 2026-04-06
- Symptom: The tool returns raw page content, or nothing, and does not return tag suggestions.
- Cause: The API does not currently return tag suggestions from that tool.
- Policy: If the API returns no suggestion, edit tags by hand. The cleanup script pre-fills the current tags.

## BF-007 — `find_misplaced_bookmarks` ignores Unsorted

- Status: open
- Date: 2026-04-06
- Symptom: Passing `collection_ids: [-1]` (Unsorted) returns no placement suggestions.
- Cause: The tool judges a bookmark against its current named collection. Unsorted has no collection identity to judge. Upstream developer-site issue 23.
- Policy: Use `find_bookmarks` with `collection_ids: [-1]` and decide placement outside that tool.
