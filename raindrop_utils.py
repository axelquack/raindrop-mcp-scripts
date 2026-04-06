"""
Raindrop.io utility library — shared by raindrop_cleanup.py and raindrop_importer.py.

Endpoint: https://api.raindrop.io/rest/v2/ai/mcp  (stateless — no session needed)
Auth:      Bearer test token from app.raindrop.io → Settings → Integrations → For Developers
Rate:      120 req/min
"""

import json
import os
import subprocess
import time

MCP_URL = "https://api.raindrop.io/rest/v2/ai/mcp"
REST_URL = "https://api.raindrop.io/rest/v1"


def _load_env():
    """Load .env from the same directory as this file. No external deps required."""
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
# Core MCP call (stateless — no initialize handshake needed)
# ---------------------------------------------------------------------------

def mcp_call(tool_name: str, arguments: dict) -> dict:
    """Call a Raindrop MCP tool. Returns the parsed response dict."""
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


def get_text(res: dict) -> str | None:
    """Extract the text payload from an MCP response. Returns None on error."""
    result = res.get("result", {})
    if result.get("isError"):
        content = result.get("content", [])
        err = next((i["text"] for i in content if i.get("type") == "text"), "unknown error")
        print(f"  [API error] {err}")
        return None
    content = result.get("content", [])
    return next((i["text"] for i in content if i.get("type") == "text"), None)


# ---------------------------------------------------------------------------
# Direct REST API (more reliable than MCP for collection-scoped fetches)
# ---------------------------------------------------------------------------

def rest_get(path: str, params: dict = None) -> dict:
    """Direct Raindrop REST GET. path e.g. '/raindrops/22803193'."""
    url = REST_URL + path
    if params:
        url += "?" + "&".join(f"{k}={v}" for k, v in params.items())
    result = subprocess.run(
        ["curl", "-s", url, "-H", f"Authorization: Bearer {TOKEN}"],
        capture_output=True, text=True, timeout=60,
    )
    return json.loads(result.stdout)


def rest_put(path: str, body: dict) -> dict:
    """Direct Raindrop REST PUT. path e.g. '/raindrop/123'."""
    result = subprocess.run(
        [
            "curl", "-s", "-X", "PUT", REST_URL + path,
            "-H", "Content-Type: application/json",
            "-H", f"Authorization: Bearer {TOKEN}",
            "-d", json.dumps(body),
        ],
        capture_output=True, text=True, timeout=60,
    )
    return json.loads(result.stdout)


# ---------------------------------------------------------------------------
# Collections
# ---------------------------------------------------------------------------

def list_collections() -> list[dict]:
    """Return all collections sorted by bookmark count descending."""
    res = mcp_call("find_collections", {})
    text = get_text(res)
    if not text:
        return []
    data = json.loads(text)
    cols = data.get("collections", [])
    return sorted(cols, key=lambda c: -c.get("bookmarks_count", 0))


def collections_by_name() -> dict[str, int]:
    """Return {title.lower(): collection_id} map fetched live."""
    return {c["title"].lower(): c["collection_id"] for c in list_collections()}


# ---------------------------------------------------------------------------
# Fetching bookmarks
# ---------------------------------------------------------------------------

def fetch_all_from_collection(collection_id: int, per_page: int = 50) -> list[dict]:
    """
    Fetch all bookmarks from a collection via the direct REST API.
    More reliable than mcp_call('find_bookmarks') for specific collections.
    """
    all_items = []
    page = 0
    while True:
        r = rest_get(f"/raindrops/{collection_id}", {"perpage": per_page, "page": page})
        items = r.get("items", [])
        all_items.extend(items)
        if len(items) < per_page:
            break
        page += 1
        time.sleep(0.3)
    return all_items


def find_untagged(limit: int = 100, page: int = 0) -> list[dict]:
    """Return bookmarks with no tags."""
    res = mcp_call("find_bookmarks", {"has_tags": False, "limit": limit, "page": page})
    text = get_text(res)
    if not text:
        return []
    return json.loads(text).get("bookmarks", [])


# ---------------------------------------------------------------------------
# Updating bookmarks
# ---------------------------------------------------------------------------

def update_bookmarks(updates: list[dict], verbose: bool = True) -> dict:
    """
    Batch update bookmarks. Auto-splits into chunks of 100.
    Routes 'tags' (full replacement) via REST API, everything else via MCP.

    Each update op:
        {
            "bookmark_ids": [123],
            "update": {
                "collection_id": 8995029,   # optional — move
                "add_tags": ["tag1"],        # optional — append tags
                "tags": ["tag1", "tag2"],    # optional — replace all tags (uses REST)
                "note": "Description",       # optional — set note
            }
        }
    """
    results = {}
    mcp_ops, rest_ops = [], []
    for op in updates:
        if "tags" in op.get("update", {}):
            rest_ops.append(op)
        else:
            mcp_ops.append(op)

    # MCP path
    for i in range(0, len(mcp_ops), 100):
        batch = mcp_ops[i:i + 100]
        res = mcp_call("update_bookmarks", {"updates": batch})
        text = get_text(res)
        result = json.loads(text) if text else {}
        results[f"mcp_{i}"] = result
        if verbose:
            print(f"  Batch {i//100 + 1} ({len(batch)} ops): {result}")

    # REST path (full tag replacement)
    for op in rest_ops:
        bid = op["bookmark_ids"][0]
        new_tags = op["update"]["tags"]
        r = rest_put(f"/raindrop/{bid}", {"tags": new_tags})
        results[f"rest_{bid}"] = r.get("result")
        if verbose:
            status = "✅" if r.get("result") else "⚠️"
            print(f"  {status} Tag replace on {bid}: {new_tags}")

    return results
