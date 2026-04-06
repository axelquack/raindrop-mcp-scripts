"""
Raindrop AI Maintenance Agent
Runs AI-powered analysis of your Raindrop library and asks for approval
on each individual suggestion before applying any change.
"""

import json
import os
import subprocess
import sys

MCP_URL = "https://api.raindrop.io/rest/v2/ai/mcp"
REST_URL = "https://api.raindrop.io/rest/v1"


def _load_env():
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, val = line.partition("=")
                    os.environ.setdefault(key.strip(), val.strip().strip("\"'"))


_load_env()
TOKEN = os.environ.get("RAINDROP_TOKEN", "")


# ---------------------------------------------------------------------------
# Colors (ANSI — works in macOS Terminal and iTerm2)
# ---------------------------------------------------------------------------

class C:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    # Foreground
    WHITE   = "\033[97m"
    CYAN    = "\033[96m"
    GREEN   = "\033[92m"
    YELLOW  = "\033[93m"
    RED     = "\033[91m"
    BLUE    = "\033[94m"
    MAGENTA = "\033[95m"
    GRAY    = "\033[90m"

def header(text):
    print(f"\n{C.BOLD}{C.BLUE}{'─' * 50}{C.RESET}")
    print(f"{C.BOLD}{C.BLUE}  {text}{C.RESET}")
    print(f"{C.BOLD}{C.BLUE}{'─' * 50}{C.RESET}")

def title(text):
    return f"{C.BOLD}{C.WHITE}{text}{C.RESET}"

def tag_list(tags):
    return f"{C.YELLOW}{tags}{C.RESET}"

def suggested(tags):
    return f"{C.GREEN}{tags}{C.RESET}"

def collection_name(name):
    return f"{C.CYAN}{name}{C.RESET}"

def success(text):
    return f"{C.GREEN}{text}{C.RESET}"

def warning(text):
    return f"{C.YELLOW}{text}{C.RESET}"

def error(text):
    return f"{C.RED}{text}{C.RESET}"

def dim(text):
    return f"{C.DIM}{text}{C.RESET}"

def hint(text):
    return f"{C.GRAY}{text}{C.RESET}"


# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------

def mcp_call(tool_name, arguments):
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": arguments},
    }
    result = subprocess.run(
        [
            "curl", "-s", "-X", "POST", MCP_URL,
            "-H", "Content-Type: application/json",
            "-H", f"Authorization: Bearer {TOKEN}",
            "-d", json.dumps(payload),
        ],
        capture_output=True, text=True, timeout=60,
    )
    try:
        return json.loads(result.stdout)
    except Exception:
        return {"error": "Invalid JSON", "raw": result.stdout[:200]}


def get_text(res):
    result = res.get("result", {})
    if result.get("isError"):
        content = result.get("content", [])
        err_text = next((i["text"] for i in content if i.get("type") == "text"), "unknown error")
        print(f"  {error('[API error]')} {err_text}")
        return None
    content = result.get("content", [])
    return next((i["text"] for i in content if i.get("type") == "text"), None)


def parse_json(text):
    try:
        return json.loads(text)
    except Exception as e:
        print(f"  {error('[Parse error]')} {e} — raw: {text[:100]}")
        return None


def ask(prompt, options="y/n/s", default="n"):
    opts_display = hint(f"[{options}/q]")
    while True:
        try:
            raw = input(f"  {prompt} {opts_display}: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nAborted.")
            sys.exit(0)
        if raw == "q":
            print("Quitting.")
            sys.exit(0)
        if raw == "" and default:
            return default
        if raw in options.replace("/", ""):
            return raw
        if raw in ("y", "n", "s"):
            return raw


def apply_updates(updates):
    if not updates:
        return
    mcp_ops = []
    rest_ops = []
    for op in updates:
        if "tags" in op.get("update", {}):
            rest_ops.append(op)
        else:
            mcp_ops.append(op)

    # MCP path — add_tags, collection_id, note
    if mcp_ops:
        res = mcp_call("update_bookmarks", {"updates": mcp_ops})
        text = get_text(res)
        if text:
            data = parse_json(text)
            updated = data.get("updated", "?") if data else "?"
            print(f"  {success('✅')} {updated} bookmark(s) updated.")
        else:
            print(f"  {warning('⚠️  MCP update may have failed.')}")

    # REST path — full tag replacement
    for op in rest_ops:
        bid = op["bookmark_ids"][0]
        new_tags = op["update"]["tags"]
        result = subprocess.run(
            [
                "curl", "-s", "-X", "PUT",
                f"{REST_URL}/raindrop/{bid}",
                "-H", "Content-Type: application/json",
                "-H", f"Authorization: Bearer {TOKEN}",
                "-d", json.dumps({"tags": new_tags}),
            ],
            capture_output=True, text=True, timeout=30,
        )
        try:
            data = json.loads(result.stdout)
            if data.get("result") is True:
                print(f"  {success('✅')} Tags updated to: {suggested(new_tags)}")
            else:
                print(f"  {error('⚠️  REST update failed:')} {result.stdout[:100]}")
        except Exception:
            print(f"  {error('⚠️  Could not parse REST response:')} {result.stdout[:100]}")


# ---------------------------------------------------------------------------
# Collection chooser (shared between steps)
# ---------------------------------------------------------------------------

def pick_collection(collections):
    """Show a numbered, hierarchical collection chooser. Returns collection dict or None."""
    valid = [c for c in collections if c["collection_id"] > 0]
    children = {}
    for c in valid:
        pid = c.get("parent_id") or c.get("parent", {})
        if isinstance(pid, dict):
            pid = pid.get("$id") or pid.get("_id")
        children.setdefault(pid, []).append(c)

    ordered = []
    def add_level(parent_id, indent):
        for c in sorted(children.get(parent_id, []), key=lambda x: x["title"].lower()):
            ordered.append((c, indent))
            add_level(c["collection_id"], indent + 1)
    add_level(None, 0)

    print()
    for i, (c, indent) in enumerate(ordered, 1):
        indent_str = "    " * indent
        marker = f"{C.DIM}└─{C.RESET} " if indent else ""
        num = f"{C.CYAN}{i:>3}.{C.RESET}"
        print(f"  {num}  {indent_str}{marker}{c['title']}")
    print()

    try:
        pick = input(f"  {hint('Pick number (Enter to cancel):')} ").strip()
    except (EOFError, KeyboardInterrupt):
        return None

    if pick.isdigit():
        idx = int(pick) - 1
        if 0 <= idx < len(ordered):
            return ordered[idx][0]
    return None


# ---------------------------------------------------------------------------
# Step 1 — Popular themes / keywords
# ---------------------------------------------------------------------------

def step_popular_themes():
    header("Step 1 — Library Theme Discovery")

    res = mcp_call("fetch_popular_keywords", {})
    text = get_text(res)
    if not text:
        print(f"  {warning('Could not fetch themes.')}")
        return

    keywords = [k.strip() for k in text.split(",") if k.strip()]
    print(f"  Top themes across your library {dim(f'({len(keywords)} found)')}:\n")
    for i in range(0, min(30, len(keywords)), 5):
        row = "   ".join(f"{C.CYAN}•{C.RESET} {k}" for k in keywords[i:i+5])
        print(f"  {row}")


# ---------------------------------------------------------------------------
# Step 2 — Misplaced bookmarks
# ---------------------------------------------------------------------------

def step_misplaced_bookmarks():
    header("Step 2 — Misplaced Bookmarks")

    res = mcp_call("find_collections", {})
    text = get_text(res)
    if not text:
        return
    data = parse_json(text)
    if not data:
        return

    collections = data.get("collections", [])
    col_names = {c["collection_id"]: c["title"] for c in collections}
    col_ids = [c["collection_id"] for c in collections if c.get("bookmarks_count", 0) > 5][:15]

    if not col_ids:
        print(f"  {warning('No collections with enough bookmarks to analyse.')}")
        return

    print(f"  Scanning {C.CYAN}{len(col_ids)}{C.RESET} collections…")
    res = mcp_call("find_misplaced_bookmarks", {"collection_ids": col_ids})
    text = get_text(res)
    if not text:
        return

    data = parse_json(text)
    if not data:
        return

    suggestions = data.get("bookmarks", data.get("items", []))
    if not suggestions:
        print(f"  {success('✅ All bookmarks appear correctly placed!')}")
        return

    print(f"\n  {C.BOLD}AI flagged {C.YELLOW}{len(suggestions)}{C.RESET}{C.BOLD} potentially misplaced bookmarks.{C.RESET}")
    print(f"  {hint('y=move suggested  m=move elsewhere  f=flag  n=skip  s=skip rest  q=quit')}\n")

    for s in suggestions:
        bid = s.get("bookmark_id") or s.get("_id")
        t = (s.get("title") or "Unknown")[:58]
        curr_id = s.get("collection_id")
        sugg_id = s.get("suggested_collection_id")
        curr_name = col_names.get(curr_id, str(curr_id))
        sugg_name = col_names.get(sugg_id, str(sugg_id)) if sugg_id else None

        print(f"  {title(repr(t))}")
        print(f"    Current:   {collection_name(curr_name)}")

        if sugg_id and sugg_id != curr_id:
            print(f"    Suggested: {suggested(sugg_name)}")
        else:
            print(f"    {dim('No specific suggestion — flagged as outlier.')}")

        try:
            raw = input(f"  {C.GRAY}>{C.RESET} ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            sys.exit(0)

        if raw == "q":
            sys.exit(0)
        if raw == "s":
            break
        if raw in ("n", ""):
            print()
            continue
        if raw == "y" and sugg_id and sugg_id != curr_id:
            apply_updates([{"bookmark_ids": [bid], "update": {"collection_id": sugg_id}}])
        elif raw == "f":
            apply_updates([{"bookmark_ids": [bid], "update": {"add_tags": ["review"]}}])
        elif raw == "m":
            chosen = pick_collection(collections)
            if chosen:
                apply_updates([{"bookmark_ids": [bid], "update": {"collection_id": chosen["collection_id"]}}])
                print(f"    Moved to: {collection_name(chosen['title'])}")
            else:
                print(f"    {dim('Cancelled.')}")
        print()


# ---------------------------------------------------------------------------
# Step 3 — Mistagged bookmarks
# ---------------------------------------------------------------------------

def fetch_suggested_tags(bid):
    res = mcp_call("fetch_bookmark_content", {"bookmark_id": bid})
    text = get_text(res)
    if not text:
        return []
    data = parse_json(text)
    if data:
        for field in ("tags", "keywords", "suggested_tags", "suggested_keywords", "labels"):
            val = data.get(field)
            if val and isinstance(val, list):
                return [str(t).strip() for t in val if t]
            if val and isinstance(val, str):
                return [t.strip() for t in val.split(",") if t.strip()]
        for val in data.values():
            if isinstance(val, list) and val and isinstance(val[0], str):
                return [str(t).strip() for t in val if t]
        return []
    return [t.strip() for t in text.split(",") if t.strip()][:15]


def step_mistagged_bookmarks():
    header("Step 3 — Inconsistent Tags")

    res = mcp_call("find_tags", {"bookmarks_count": {"gte": 3}})
    text = get_text(res)
    if not text:
        return
    data = parse_json(text)
    if not data:
        return

    tags = [t["tag"] for t in data.get("tags", [])][:20]
    if not tags:
        print(f"  {warning('Not enough tagged bookmarks to analyse.')}")
        return

    print(f"  Analysing {C.CYAN}{len(tags)}{C.RESET} tags: {dim(', '.join(tags[:10]))}…")
    res = mcp_call("find_mistagged_bookmarks", {"tags": tags})
    text = get_text(res)
    if not text:
        return

    data = parse_json(text)
    if not data:
        return

    items = data.get("bookmarks", data.get("items", []))
    if not items:
        print(f"  {success('✅ No inconsistent tags detected.')}")
        return

    print(f"\n  {C.BOLD}AI found {C.YELLOW}{len(items)}{C.RESET}{C.BOLD} bookmarks with potentially wrong tags.{C.RESET}")
    print(f"  {hint('y=accept  e=edit  f=flag  n=skip  s=skip rest  q=quit')}\n")

    for item in items:
        bid = item.get("bookmark_id") or item.get("_id")
        t = (item.get("title") or "Unknown")[:60]
        link = item.get("link", "")
        current_tags = item.get("tags", [])

        print(f"  {title(repr(t))}")
        print(f"    {dim(link[:72])}")
        print(f"    Tags now:  {tag_list(current_tags)}")

        print(f"  {dim('Fetching suggestions…')}", end=" ", flush=True)
        sugg = fetch_suggested_tags(bid)
        if sugg:
            print(f"{suggested(sugg)}")
        else:
            print(dim("none available."))

        try:
            raw = input(f"  {C.GRAY}>{C.RESET} ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nAborted.")
            sys.exit(0)

        if raw == "q":
            sys.exit(0)
        if raw == "s":
            break
        if raw in ("n", ""):
            print()
            continue
        if raw == "f":
            apply_updates([{"bookmark_ids": [bid], "update": {"add_tags": ["review"]}}])
        elif raw == "y" and sugg:
            apply_updates([{"bookmark_ids": [bid], "update": {"tags": sugg}}])
        elif raw in ("e", "y"):
            prefill = ", ".join(sugg) if sugg else ", ".join(current_tags)
            print(f"    {dim(f'Edit tags (Enter to accept: {prefill})')}")
            try:
                edited = input(f"    {C.GRAY}>{C.RESET} ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                continue
            if edited:
                new_tags = [t.strip() for t in edited.split(",") if t.strip()]
                apply_updates([{"bookmark_ids": [bid], "update": {"tags": new_tags}}])
            elif sugg:
                apply_updates([{"bookmark_ids": [bid], "update": {"tags": sugg}}])
        print()


# ---------------------------------------------------------------------------
# Step 4 — Broken links
# ---------------------------------------------------------------------------

def step_broken_links():
    header("Step 4 — Broken Links")

    res = mcp_call("find_bookmarks", {"search": "broken:true", "limit": 25})
    text = get_text(res)

    broken = []
    if text:
        data = parse_json(text)
        if data:
            broken = data.get("bookmarks", data.get("items", []))

    if not broken:
        result = subprocess.run(
            [
                "curl", "-s",
                f"{REST_URL}/raindrops/0?broken=true&perpage=25",
                "-H", f"Authorization: Bearer {TOKEN}",
            ],
            capture_output=True, text=True, timeout=30,
        )
        try:
            rest_data = json.loads(result.stdout)
            broken = rest_data.get("items", [])
            for b in broken:
                b["bookmark_id"] = b.get("_id")
        except Exception:
            pass

    if not broken:
        print(f"  {success('✅ No broken links found.')}")
        return

    # These domains block automated checkers — always false positives
    FALSE_POSITIVE_DOMAINS = {
        "youtube.com", "youtu.be",
        "twitter.com", "x.com",
        "instagram.com", "linkedin.com",
        "facebook.com", "reddit.com",
        "imgur.com",
        "github.com", "gist.github.com",
        "algolia.com", "hn.algolia.com",
        "medium.com",
        "notion.so",
        "docs.google.com", "drive.google.com",
        "apple.com", "apps.apple.com",
        "amazon.com", "amzn.to",
        "vimeo.com",
        "tiktok.com",
    }

    def is_false_positive(link):
        for domain in FALSE_POSITIVE_DOMAINS:
            if domain in link:
                return True
        return False

    real_broken = [b for b in broken if not is_false_positive(b.get("link", ""))]
    skipped = len(broken) - len(real_broken)

    if skipped:
        print(f"  {dim(f'Skipped {skipped} false positive(s) — YouTube, Twitter, Instagram etc. block link checkers.')}")

    if not real_broken:
        print(f"  {success('✅ No genuinely broken links found.')}")
        return

    print(f"\n  {C.BOLD}Found {C.RED}{len(real_broken)}{C.RESET}{C.BOLD} potentially broken links.{C.RESET}")
    print(f"  {dim('Review and delete manually in Raindrop if needed.')}\n")

    for b in real_broken:
        t = (b.get("title") or "Unknown")[:58]
        link = b.get("link", "")
        print(f"  {title(repr(t))}")
        print(f"    {error(link[:72])}")
        print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print(f"\n{C.BOLD}{C.BLUE}{'=' * 50}{C.RESET}")
    print(f"{C.BOLD}{C.BLUE}   RAINDROP AI MAINTENANCE AGENT{C.RESET}")
    print(f"{C.BOLD}{C.BLUE}{'=' * 50}{C.RESET}")
    print(f"  {hint('y=yes  n=no  s=skip step  q=quit')}")

    steps = [
        ("Popular themes",       step_popular_themes),
        ("Misplaced bookmarks",  step_misplaced_bookmarks),
        ("Inconsistent tags",    step_mistagged_bookmarks),
        ("Broken links",         step_broken_links),
    ]

    for name, fn in steps:
        try:
            fn()
        except KeyboardInterrupt:
            print(f"\n  {dim('Skipping step…')}")
            continue
        except Exception as e:
            print(f"\n  {error(f'[Error in {repr(name)}]')} {e}")
            continue

    print(f"\n{C.BOLD}{C.BLUE}{'=' * 50}{C.RESET}")
    print(f"{C.BOLD}{C.GREEN}  Maintenance session complete.{C.RESET}")
    print(f"{C.BOLD}{C.BLUE}{'=' * 50}{C.RESET}\n")


if __name__ == "__main__":
    main()
