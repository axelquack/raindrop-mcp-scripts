import json
import os
import re
import subprocess
import sys
import time

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


def mcp_call(tool_name, arguments):
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": arguments},
    }
    result = subprocess.run(
        [
            "curl",
            "-s",
            "-X",
            "POST",
            MCP_URL,
            "-H",
            "Content-Type: application/json",
            "-H",
            f"Authorization: Bearer {TOKEN}",
            "-d",
            json.dumps(payload),
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    try:
        return json.loads(result.stdout)
    except:
        return {"error": "Invalid JSON", "stdout": result.stdout}



def extract_url_from_webloc(file_path):
    try:
        result = subprocess.run(
            ["plutil", "-p", file_path],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
        for line in result.stdout.splitlines():
            if '"URL"' in line:
                return line.split('=> "')[1].rstrip('"')
    except:
        pass
    try:
        with open(file_path, "rb") as f:
            content = f.read()
            urls = re.findall(rb'https?://[^\s<>"\x00-\x1f\x7f-\xff]+', content)
            for url_bytes in reversed(urls):
                url = url_bytes.decode("utf-8", errors="ignore")
                if "apple.com/DTDs" not in url:
                    return url
    except:
        pass
    return None


def extract_links_from_md(file_path):
    links = []
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            md_match = re.search(r"\[([^\]]+)\]\((https?://[^\s\)]+)\)", line)
            if md_match:
                links.append({"title": md_match.group(1), "url": md_match.group(2)})
                continue
            url_match = re.search(r"(https?://[^\s]+)", line)
            if url_match:
                url = url_match.group(1).rstrip(".,;)]")
                title = line.replace(url, "").replace("*", "").strip() or url
                links.append({"title": title, "url": url})
    return links



def upload_batch(items, metadata):
    res = mcp_call("create_bookmarks", {"create": items})
    if "result" in res and not res.get("isError"):
        content = res["result"].get("content", [])
        text = next(
            (item["text"] for item in content if item.get("type") == "text"), None
        )
        if text:
            # Response handling for both single dict and list
            parsed = json.loads(text)
            created = parsed.get("created", []) if isinstance(parsed, dict) else parsed
            updates = []
            new_ids = []
            for j, b in enumerate(created):
                bid = b.get("bookmark_id") or b.get("_id")
                if bid:
                    new_ids.append(bid)
                    updates.append(
                        {
                            "bookmark_ids": [bid],
                            "update": {"add_tags": metadata[j]["tags"]},
                        }
                    )
            if updates:
                mcp_call("update_bookmarks", {"updates": updates})
            return new_ids
    return []



def main():
    print("=== Raindrop Importer ===")
    print("Bookmarks are imported to Unsorted. Run raindrop_cleanup.py afterwards to sort and tag.\n")

    while True:
        print("\n[1] Markdown File\n[2] Folder of .webloc files")
        choice = input("Select input method (1 or 2): ").strip()
        if choice in ("1", "2"):
            break
        print(f"  Invalid input {repr(choice)} — please enter 1 or 2.")

    path = input("Enter the full path: ").strip()

    links_to_process = []
    is_webloc = False

    if choice == "1":
        if not os.path.isfile(path):
            print(f"Error: '{path}' is not a file.")
            return
        links_to_process = extract_links_from_md(path)
    elif choice == "2":
        if not os.path.isdir(path):
            print(f"Error: '{path}' is not a directory.")
            return
        is_webloc = True
        for f in os.listdir(path):
            if f.endswith(".webloc"):
                full_path = os.path.join(path, f)
                url = extract_url_from_webloc(full_path)
                if url:
                    links_to_process.append(
                        {
                            "title": f.replace(".webloc", ""),
                            "url": url,
                            "path": full_path,
                        }
                    )
    else:
        print("Invalid choice.")
        return

    total = len(links_to_process)
    print(f"Found {total} links to process.")

    all_new_ids = []

    batch_size = 50
    for i in range(0, total, batch_size):
        chunk = links_to_process[i : i + batch_size]
        print(f"Processing batch {i // batch_size + 1}...")

        items, meta = [], []
        for l in chunk:
            items.append(
                {
                    "link": l["url"],
                    "title": l["title"],
                    "collection_id": -1,
                    "note": "Imported via Unified Script",
                }
            )
            meta.append({"tags": ["imported"]})

        new_ids = upload_batch(items, meta)
        if new_ids:
            all_new_ids.extend(new_ids)
            print(f"Successfully uploaded {len(new_ids)} links.")
            if is_webloc:
                for l in chunk:
                    try:
                        os.remove(l["path"])
                    except:
                        pass

        time.sleep(1.5)

    print(f"\nDone! {len(all_new_ids)} bookmark(s) added to Unsorted.")
    print("Run raindrop_cleanup.py to sort and tag them.")


if __name__ == "__main__":
    main()
