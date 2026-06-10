"""Inline tools/watches.json into tools/tile_picker.html.

The picker reads its device list from an inline <script type="application/json"
id="watches-data"> block so the page works under file:// where fetch() of
local JSON is blocked. This script keeps the inline copy in sync with the
canonical tools/watches.json after edits.

Run after editing watches.json. Idempotent.
"""
from pathlib import Path
import re

REPO = Path(__file__).resolve().parent.parent
HTML = REPO / "tools" / "tile_picker.html"
JSON = REPO / "tools" / "watches.json"

html = HTML.read_text(encoding="utf-8")
data = JSON.read_text(encoding="utf-8").strip()

# Replace whatever is currently between the open/close <script id="watches-data"> tags.
pattern = re.compile(
    r'(<script type="application/json" id="watches-data">)(.*?)(</script>)',
    re.DOTALL,
)
m = pattern.search(html)
if not m:
    raise SystemExit("could not find <script id='watches-data'> in tile_picker.html")

new = html[:m.start()] + m.group(1) + "\n" + data + "\n    " + m.group(3) + html[m.end():]
HTML.write_text(new, encoding="utf-8")
print(f"inlined {JSON.name} ({len(data)} bytes) into {HTML.name}")
