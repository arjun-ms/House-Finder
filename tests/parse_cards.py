"""Extract the full HTML of individual property cards from the pdpid page."""
import re, sys
sys.stdout.reconfigure(encoding='utf-8')

with open("tests/fixtures/detail_page_pdpid.html", "r", encoding="utf-8") as f:
    html = f.read()

# Find all pdp__prop__card sections
# These are the individual rental listings within a project page
card_starts = [m.start() for m in re.finditer(r'class="pdp__prop__card "', html)]
print(f"Found {len(card_starts)} property cards")

for i, start in enumerate(card_starts[:3]):
    # Extract a chunk around each card (roughly 3000 chars should cover one card)
    chunk = html[start:start+3000]
    # Strip tags for readability
    text = re.sub(r'<[^>]+>', ' | ', chunk)
    text = re.sub(r'\s+', ' ', text).strip()
    print(f"\n=== CARD {i+1} (raw text) ===")
    print(text[:500])
    print(f"\n=== CARD {i+1} (raw HTML, first 2000 chars) ===")
    print(chunk[:2000])
    print("---")

# Also look at the card detail subclasses
print("\n\n=== All pdp__prop__card__* subclasses ===")
subcls = re.findall(r'class="(pdp__prop__card__[^"]*)"', html)
for c in sorted(set(subcls)):
    print(f"  {c}")

# Find what pdp__prop__card__detail contains
print("\n=== pdp__prop__card__detail content ===")
detail_starts = [m.start() for m in re.finditer(r'class="pdp__prop__card__detail"', html)]
for i, start in enumerate(detail_starts[:3]):
    chunk = html[start:start+1500]
    text = re.sub(r'<[^>]+>', ' | ', chunk)
    text = re.sub(r'\s+', ' ', text).strip()
    print(f"\n  Card {i+1} detail: {text[:300]}")

# Find what pdp__prop__card__item contains
print("\n=== pdp__prop__card__item content ===")
item_starts = [m.start() for m in re.finditer(r'class="pdp__prop__card__item"', html)]
for i, start in enumerate(item_starts[:10]):
    chunk = html[start:start+500]
    text = re.sub(r'<[^>]+>', ' | ', chunk)
    text = re.sub(r'\s+', ' ', text).strip()
    print(f"  Item {i+1}: {text[:150]}")
