import re
import os
import urllib.request
import time

log_path = r"C:\Users\shant\.gemini\antigravity\brain\dcb39820-6575-452d-8267-8488478715b4\.system_generated\tasks\task-808.log"

def process_log():
    if not os.path.exists(log_path):
        return
    with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()

    pattern = re.compile(
        r'Failed to download (d:\\Projects\\AG\\spherex-planet-x\\data\\drive\\[^\r\n]+?):\s*Failed to retrieve file url:.*?https://drive\.google\.com/uc\?id=([a-zA-Z0-9_-]+)',
        re.DOTALL
    )
    matches = pattern.findall(text)

    for path, doc_id in matches:
        if os.path.exists(path) and os.path.getsize(path) > 100:
            continue
        os.makedirs(os.path.dirname(path), exist_ok=True)
        # Try doc export
        success = False
        for fmt in ["txt", "csv", "docx"]:
            url = f"https://docs.google.com/document/d/{doc_id}/export?format={fmt}" if fmt in ["txt", "docx"] else f"https://docs.google.com/spreadsheets/d/{doc_id}/export?format={fmt}"
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    content = resp.read()
                    if len(content) > 50:
                        with open(path, "wb") as out_f:
                            out_f.write(content)
                        print(f"SUCCESS: {os.path.basename(path)} ({len(content)} bytes via {fmt})")
                        success = True
                        break
            except Exception:
                continue
        if not success:
            print(f"SKIPPED/UNAVAILABLE: {os.path.basename(path)}")

if __name__ == "__main__":
    process_log()
