# Roadmap

Last reviewed: 2026-11-13 (Europe/Berlin)

See also `TODO.md`, `CHANGELOG.md`, and `BUGFIXES.md`.

The Ideas table replaces `IDEAS.md`. Do not keep a separate ideas file. This repository had no `IDEAS.md`, `docs/roadmap.md`, or `PLAN.md` to fold in.

## Now

- None.

## Next

- None.

## Later

- None.

## Ideas

| Idea | Why it can wait | Added |
| --- | --- | --- |
| Show tag suggestions in the cleanup CLI | The API returns flagged bookmarks and does not return suggested tags. Upstream developer-site issue 22 | 2026-04-06 |
| Set collection icons from a script | The API does not accept an icon or emoji field. Upstream developer-site issue 26 | 2026-04-06 |
| Treat broken-link results as final | Several public sites block automated checkers. The false-positive list in `raindrop_cleanup.py` is not exhaustive | 2026-04-06 |
| Use MCP `find_bookmarks` for one collection | That call can return an unknown error. `fetch_all_from_collection` uses REST instead. Upstream developer-site issue 25 | 2026-04-06 |

## Done recently

- 2026-11-13 — Public repo standard applied. License is PolyForm Noncommercial 1.0.0. Older published versions stay under Apache-2.0.
- 2026-11-12 — Standing documentation, commit, and push rule added to `AGENTS.md`.
- 2026-04-06 — Importer, interactive cleanup script, and shared utils.
