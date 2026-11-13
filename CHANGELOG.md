# Changelog

This file is published with a public repository.

It must never contain IP addresses, hostnames, MAC addresses, internal paths, usernames, email addresses, vault IDs, credentials, or pane IDs.

Detailed private notes may go into `CHANGELOG.private.md`. That file is gitignored in a public repository. Do not commit it.

Newest first. Dates are Europe/Berlin, `YYYY-MM-DD`.

Use one heading per change: `## YYYY-MM-DD — title`. Under it, keep only the subsections that have items. End with a Why line.

This file is the public record. There was no earlier changelog in the tree. Older notes below are taken from the commit subjects. They do not repeat example identifiers.

## 2026-11-13 — Public repo standard

### Added

- The repo-standard file set: `AGENTS.md` skeleton, `CLAUDE.md` symlink, `ROADMAP.md`, `TODO.md`, `BUGFIXES.md`, `SECURITY.md`, `justfile`, `just/code.just`, `.githooks/pre-commit`, `scripts/check-secrets.sh`, `scripts/lint.sh`, `scripts/docs-index.sh`, `scripts/repo-audit.sh`, `.gitleaks.toml`, `.github/workflows/gitleaks.yml`, and `docs/README.md`.
- Public gitignore rules so `HANDOFF.md` and `CHANGELOG.private.md` stay untracked. The existing `secrets/` ignore stays.
- `BUGFIXES.md` records the lasting API limits (`BF-001` through `BF-007`) that the README already described.

### Changed

- `LICENSE` is PolyForm Noncommercial 1.0.0. Versions published before this commit remain available under Apache-2.0. Axel is the sole contributor.
- `README.md` follows the repo-standard layout and keeps the script guide. Example collection ids in the README and in `raindrop_utils.py` comments are placeholders.
- `AGENTS.md` follows the skeleton and keeps the standing documentation rule. The Herdr agent line is Signe (Bookmarks) · Raindrop bulk scripts.
- `.env.example` still names `RAINDROP_TOKEN` and leaves the value empty.
- Nothing was folded from `IDEAS.md`, `CLAUDE.md`, `docs/roadmap.md`, or `PLAN.md`. Those files were not in the tree. `CLAUDE.md` is a new symlink to `AGENTS.md`. No session notes were moved.

### Security

- Branch protection on main (set by Shepherd on GitHub): pull request required (0 approvals, administrators included), force-push and deletion blocked. From now on changes reach the default branch through a pull request.
- `pre-commit` runs `scripts/check-secrets.sh --staged` after `just setup`.
- GitHub Actions runs gitleaks on push and pull_request.

**Why:** This public repository needs an explicit license, a secret check, and a file map before further edits.

## 2026-11-12 — Documentation, commit, and push

### Added

- The standing rule in `AGENTS.md` for documenting a change, secret-checking the staged diff, and pushing the existing remote only after that check.

**Why:** Agents working in this repo share one secret check before commit and push.

## 2026-04-06 — Bookmark scripts

### Added

- `raindrop_utils.py`, `raindrop_importer.py`, and `raindrop_cleanup.py`.
- `README.md`, `.gitignore`, and `.env.example` (the setting name only).

### Changed

- `update_bookmarks` sends a full tag replacement through REST and splits a combined remove-plus-add into two MCP calls.
- The README records the API limits and links the upstream issue numbers.

**Why:** Import bookmarks, then clean and retag them from the command line, without a third-party Python package.
