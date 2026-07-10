"""Parse the single listing detail page HTML."""
import re, sys
sys.stdout.reconfigure(encoding='utf-8')

with open("tests/fixtures/detail_page_single.html", "r", encoding="utf-8") as f:
    html = f.read()

print(f"Total HTML length: {len(html)} chars")
print(f"\nFull content (first 5000 chars):\n")
print(html[:5000])
