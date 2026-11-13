Herdr agent: Signe (Bookmarks) · Raindrop bulk scripts

Lead bot: Signe / Visibility: public / Default branch: main / Push: PR only

`CLAUDE.md` is a symlink to `AGENTS.md` (`ln -sf AGENTS.md CLAUDE.md`). Edit `AGENTS.md` only. Do not keep a second copy.

## Role

### Project

Three Python scripts for bulk work on a Raindrop.io bookmark library. `raindrop_importer.py` imports `.webloc` files or Markdown links into Unsorted with the tag `imported`. `raindrop_cleanup.py` is an interactive four-step pass (themes, misplaced bookmarks, tags, broken links) and asks before each change. `raindrop_utils.py` is the shared library: stateless MCP calls, REST for collection fetches and full tag replacement, and an automatic split when `remove_tags` and `add_tags` are in one update. Python 3.10+ and `curl`. No third-party packages. Raindrop Pro is required for the MCP API and the AI tools. The rate limit is 120 requests per minute. The MCP endpoint needs no initialize handshake.

`raindrop_utils.py` names `raindrop-bookmark-management.md`. That file is not in this repository. Do not add it.

Live-infra rule (Axel, 2026-11-13): this agent works on repo files only. Never run `raindrop_cleanup.py`, `raindrop_importer.py`, or anything that calls the Raindrop API. Those scripts change bookmarks. Validate with `python -m py_compile` and offline lint only. Never open `.env`. Keep `.env.example`. No commands against hosts, devices, VMs, or containers.

### This agent owns

- `raindrop_cleanup.py`, `raindrop_importer.py`, and `raindrop_utils.py` as source.
- The public docs and the repo-standard files in the file map.
- Offline checks: `python -m py_compile` and `just lint` / `just check`.

### Out of scope & handoff

- Running the scripts, or any call to the Raindrop API. Axel runs those.
- Opening `.env`, or copying a token into git.
- Other repositories. Do not edit agent-platform from this tree. The public handoff belongs in that repository. Do not write it from here.
- Commands against hosts, devices, VMs, or containers.

## Start here

Read in this order:

1. `AGENTS.md` (this file).
2. `README.md`.
3. `BUGFIXES.md` and `SECURITY.md`.
4. `HANDOFF.md`, the last three entries in `CHANGELOG.md`, and `git log -5`. In this public repo `HANDOFF.md` is gitignored. The public handoff lives in the agent-platform repository at `handoffs/<repo>.md`. Do not write that note from this tree.
5. The current ticket, or else `TODO.md` and `ROADMAP.md`.
6. `docs/README.md`.

## File map

| File | What it is for | Who updates it |
| --- | --- | --- |
| `.env.example` | Setting name for the Raindrop token. Empty value. No secret | Whoever adds a setting |
| `.githooks/pre-commit` | Runs `scripts/check-secrets.sh --staged` | Whoever changes the check |
| `.github/workflows/gitleaks.yml` | Gitleaks on push and pull_request | Whoever changes the CI check |
| `.gitignore` | Base ignore rules plus the public fragment. Keeps `HANDOFF.md` and `CHANGELOG.private.md` untracked. Also ignores `secrets/` | Whoever changes ignore rules |
| `.gitleaks.toml` | Gitleaks rules and the license-text allowlist | Whoever changes the secret check |
| `AGENTS.md` | Rules for the herdr agent | The owning agent, when the role or the rules change |
| `BUGFIXES.md` | Durable bug writeups, `BF-NNN`. Lasting API limits | Whoever records the fix |
| `CHANGELOG.md` | What changed, newest first, with a why. Public variant | Whoever makes the change |
| `CLAUDE.md` | Symlink to `AGENTS.md`. Same text. No second copy | Nobody. Recreate it with `ln -sf AGENTS.md CLAUDE.md` |
| `HANDOFF.md` | Done, next, and open questions. Gitignored in this public repo. The note lives in the agent-platform handoff folder | The agent, before stopping. Do not commit this file |
| `LICENSE` | PolyForm Noncommercial 1.0.0. Axel is the sole contributor | Axel |
| `README.md` | What the repo is, the status line, the script guide, and where to start | The person who changes the project |
| `ROADMAP.md` | Now, next, later, ideas, and done recently | The owning agent, when the plan moves |
| `SECURITY.md` | Threat model, where secrets live, and leak response | The owning agent, when the threat model changes |
| `TODO.md` | Interim task list until the agent-ops board exists | The agent who holds the work |
| `docs/README.md` | Contributor index of every page under `docs/` | Whoever adds or removes a docs page |
| `just/code.just` | Code recipes. `test` is `py_compile`. No recipe runs the Raindrop scripts | Whoever adds a recipe |
| `justfile` | Repeatable recipes, including the secret check. Imports `just/code.just` | Whoever adds a recipe |
| `raindrop_cleanup.py` | Interactive maintenance. Asks before each change. Do not run it from an agent pass | Signe, when the cleanup behavior changes |
| `raindrop_importer.py` | Import from `.webloc` files or Markdown into Unsorted. Do not run it from an agent pass | Signe, when the importer changes |
| `raindrop_utils.py` | Shared MCP and REST helpers used by the other two scripts | Signe, when the shared helpers change |
| `scripts/check-secrets.sh` | Fails when a secret-shaped file name or a gitleaks finding is in scope | Whoever changes the check |
| `scripts/docs-index.sh` | Refresh the generated list in `docs/README.md` | Whoever changes the index |
| `scripts/lint.sh` | Shellcheck the scripts and hooks, then reject whitespace errors | Whoever changes the check |
| `scripts/repo-audit.sh` | Report standard files that are missing | Whoever changes the standard |

## Hard limits

- Secrets never go into git. No tokens, auth keys, `.env` files other than `.env.example`, `auth.json`, credential files, private keys, or session exports. Use a placeholder such as `<SECRET>`.
- This repository is public. Never add IP addresses, hostnames, MAC addresses, internal paths, home paths, usernames, email addresses, vault IDs, credentials, or pane IDs.
- Never open `.env`. Keep `.env.example`. The example holds the setting name and an empty value.
- Live-infra rule (Axel, 2026-11-13): repo files only. Never run `raindrop_cleanup.py`, `raindrop_importer.py`, or anything that calls the Raindrop API. Those scripts change bookmarks. Validate with `python -m py_compile` and offline lint only. No commands against hosts, devices, VMs, or containers.
- Do not commit `HANDOFF.md` or `CHANGELOG.private.md`.
- Do not edit agent-platform from this tree.
- Stage by explicit path. Do not use `git add -A` or `git add .`.
- No force-push. A history rewrite needs Axel's approval.
- Mark anything you have not verified as **unverified**.

## Workflow

- Work through tickets and pull requests when the agent-ops board exists. Until then, track the task in `TODO.md`.
- One ticket at a time. Write a holder line on the ticket before you start, so two agents do not take the same ticket.
- Push is PR only. Branch protection on main (set by Shepherd on GitHub): pull request required (0 approvals, administrators included), force-push and deletion blocked. Open a pull request against `main`. Axel or a lead merges. Do not push the default branch directly.
- Stage by explicit path. Do not use `git add -A` or `git add .`.
- No force-push. A history rewrite needs Axel's approval.
- Before each commit, run `git diff --cached --name-only`, `git diff --cached`, and `scripts/check-secrets.sh --staged` (gitleaks). On a public repo, review `git diff @{u}..HEAD` before pushing. Nothing pushed may contain IP addresses, hostnames, internal paths, pane IDs, email addresses, or credentials.
- If a permission question or a blocker cannot be resolved, stop and say so.
- `just test` is `python3 -m py_compile` on the three scripts. It does not call the API. Do not add a recipe that runs `raindrop_cleanup.py` or `raindrop_importer.py`.

## Documentation, commit & push

Standing rule from Axel (2026-11-12), for every Grok bot and herdr agent working in this repo:

- Document every change in this project: README, `docs/`, and the changelog (`CHANGELOG.md` or `docs/changelog.md`), with date and what/why.
- Commit with a clear message, then push to the repo's existing remote, public or private, after the secret check.
- Before each commit, run a secret check: `git diff --cached --name-only` and `git diff --cached`. Never commit `.env*`, keys, tokens, `auth.json`, credentials, session exports, or `*.bak*` files. If one is staged, unstage it and add it to `.gitignore`.
- Public repos (`gh repo view --json visibility`): be extra strict. Before pushing, review the full diff being pushed (`git diff @{u}..HEAD`) for secrets, tokens, private IPs and hostnames the repo does not already contain, personal data, and session exports. If anything looks sensitive, do not push; report it to Axel.
- If the repo has no remote, commit locally and report that.
- Commit only your own change; do not sweep in someone else's uncommitted work.

## Secrets

Secrets live in Proton Pass, in the local Grok env file outside this repository, or on Axel's secure secret cards. They do not live in this repository.

The Raindrop test token belongs in the gitignored `.env` on the machine that runs the scripts. `.env.example` lists `RAINDROP_TOKEN` and leaves the value empty.

Before every commit, run:

```
git diff --cached --name-only
git diff --cached
scripts/check-secrets.sh --staged
```

The `pre-commit` hook runs `scripts/check-secrets.sh --staged` after `just setup`.

If a secret was committed: rotate it first, tell Axel, and do not rewrite history unless Axel approves the force-push.

## Handoff

Before you stop, write what you did, what is next, and the open questions.

In a private repository, update `HANDOFF.md` and keep it tracked.

In a public repository, `HANDOFF.md` is gitignored. Write the note in the agent-platform repository at `handoffs/<repo>.md`. Do not commit `HANDOFF.md` here, and do not write that note from this tree.

## Work tracking

Rule from the owner (2026-11-13): all open work goes on the owner's private GitHub Project board, not into new TODO.md items or chat-only lists.

1. File an issue in this repo (or a draft item on the board if no repo fits) and add it to the board with `gh project item-add` (find the board with `gh project list --owner @me`).
2. Link each pull request to its issue (`Closes #<n>` in the PR body) and add the PR to the board too.
3. Set **Status** (Inbox / Waiting on Axel / In progress / Done) and **Owner** (your agent or bot name; if your name is not an Owner option yet, pick your lead bot and write your name in the item).
4. Anything that needs the owner gets Status "Waiting on Axel" and the `waiting-on-axel` label. Ping the owner only if it is urgent; the morning digest covers the rest.
5. Use `gh` on the owner's machine (it has the `project` scope). The GitHub connector cannot reach personal Projects.
6. Existing TODO.md files stay for now; do not add new items to them.
