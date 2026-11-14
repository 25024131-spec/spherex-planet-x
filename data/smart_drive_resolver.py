"""
Smart Drive Resolver (Multithreaded Concurrent Engine):
Parses task-808.log and downloads every file that failed in gdown due to:
1. Google Drive virus scan warning form requirement (inputs with confirm=t, uuid, etc.)
2. Google Docs text export (export?format=txt)
3. Google Sheets csv export (export?format=csv)
"""

import os
import re
import urllib.request
import urllib.parse
import http.cookiejar
import time
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

LOG_PATH = r"C:\Users\shant\.gemini\antigravity\brain\dcb39820-6575-452d-8267-8488478715b4\.system_generated\tasks\task-808.log"

def fetch_file_robustly(file_id: str) -> bytes:
    cookie_jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))

    # Strategy 1: Google Drive usercontent download with virus scan warning bypass
    try:
        url = f"https://drive.google.com/uc?export=download&id={file_id}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with opener.open(req, timeout=30) as resp:
            data = resp.read()
            if b"accounts.google.com" not in data and b"Virus scan warning" not in data:
                return data
            text = data.decode("utf-8", errors="ignore")
            forms = re.findall(r'<form.*?action=[\'"](.*?)[\'"].*?>(.*?)</form>', text, re.DOTALL)
            if forms:
                action, body = forms[0]
                inputs = dict(re.findall(r'<input.*?name=[\'"](.*?)[\'"].*?value=[\'"](.*?)[\'"]', body))
                get_url = action + "?" + urllib.parse.urlencode(inputs)
                req2 = urllib.request.Request(get_url, headers={"User-Agent": "Mozilla/5.0"})
                with opener.open(req2, timeout=60) as resp2:
                    file_data = resp2.read()
                    if len(file_data) > 0 and b"accounts.google.com" not in file_data:
                        return file_data
    except Exception:
        pass

    # Strategy 2: Google Docs text export
    try:
        url_doc = f"https://docs.google.com/document/d/{file_id}/export?format=txt"
        req_doc = urllib.request.Request(url_doc, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req_doc, timeout=20) as resp:
            data = resp.read()
            if len(data) > 20 and b"accounts.google.com" not in data:
                return data
    except Exception:
        pass

    # Strategy 3: Google Sheets csv export
    try:
        url_sheet = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=csv"
        req_sheet = urllib.request.Request(url_sheet, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req_sheet, timeout=20) as resp:
            data = resp.read()
            if len(data) > 20 and b"accounts.google.com" not in data:
                return data
    except Exception:
        pass

    return None

def download_item(item):
    target_path, file_id = item
    if os.path.exists(target_path) and os.path.getsize(target_path) > 10:
        return target_path, True, "already_exists", os.path.getsize(target_path)

    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    file_bytes = fetch_file_robustly(file_id)
    if file_bytes and len(file_bytes) > 0:
        with open(target_path, "wb") as out_f:
            out_f.write(file_bytes)
        return target_path, True, "downloaded", len(file_bytes)
    else:
        return target_path, False, "failed", 0

def resolve_all(max_workers: int = 8):
    if not os.path.exists(LOG_PATH):
        print("Log path does not exist.")
        return

    with open(LOG_PATH, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()

    pattern = re.compile(
        r'Failed to download (d:\\Projects\\AG\\spherex-planet-x\\data\\drive\\[^\r\n]+?):\s*Failed to retrieve file url:.*?https://drive\.google\.com/uc\?id=([a-zA-Z0-9_-]+)',
        re.DOTALL
    )
    matches = pattern.findall(text)
    
    # Deduplicate matches preserving order
    seen = set()
    unique_items = []
    for p, fid in matches:
        if p not in seen:
            seen.add(p)
            unique_items.append((p, fid))

    print(f"Total unique failed items to resolve: {len(unique_items)}")

    pending = [item for item in unique_items if not (os.path.exists(item[0]) and os.path.getsize(item[0]) > 10)]
    print(f"Pending items to download: {len(pending)}")

    if not pending:
        print("All items are already downloaded and verified.")
        return

    success_count = len(unique_items) - len(pending)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {executor.submit(download_item, item): item for item in pending}
        for future in as_completed(future_map):
            target_path, ok, status, size = future.result()
            fname = os.path.basename(target_path)
            if ok:
                success_count += 1
                if status == "downloaded":
                    print(f"DOWNLOADED: {fname} ({size:,} bytes)")
            else:
                print(f"FAILED TO FETCH: {fname}")

    print(f"Done. Successfully resolved {success_count}/{len(unique_items)} files.")

if __name__ == "__main__":
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    resolve_all(max_workers=workers)
