"""Deep parse the pdpid detail page for property listing cards with floor/age/balcony/rent."""
import re, sys
sys.stdout.reconfigure(encoding='utf-8')

with open("tests/fixtures/detail_page_pdpid.html", "r", encoding="utf-8") as f:
    html = f.read()

# Search for property cards inside the pdpid page - these contain individual listings
# Look for the section that shows available flats for rent
print("=== Searching for 'prop__card' or listing cards ===")
card_classes = re.findall(r'class="([^"]*prop__card[^"]*)"', html)
unique_cards = list(set(card_classes))[:20]
for c in sorted(unique_cards):
    print(f"  {c}")

print("\n=== Searching for 'pdp__' class patterns ===")
pdp_classes = re.findall(r'class="(pdp__[^"]*)"', html)
unique_pdp = list(set(pdp_classes))[:40]
for c in sorted(unique_pdp):
    print(f"  {c}")

# Find sections with actual flat data
print("\n=== Text near '2 BHK' ===")
bhk_context = [(m.start(), html[max(0,m.start()-50):m.end()+100]) for m in re.finditer(r'2 BHK', html)]
for pos, ctx in bhk_context[:5]:
    ctx = re.sub(r'<[^>]+>', ' ', ctx).strip()
    ctx = re.sub(r'\s+', ' ', ctx)
    print(f"  @{pos}: {ctx[:120]}")

# Find the rent listings section
print("\n=== Text near rent price patterns (Rs/rupee + number) ===")
rent_ctx = [(m.start(), html[max(0,m.start()-100):m.end()+100]) for m in re.finditer(r'(?:Rs\.?|₹)\s*[\d,]+', html)]
for pos, ctx in rent_ctx[:10]:
    ctx = re.sub(r'<[^>]+>', ' ', ctx).strip()
    ctx = re.sub(r'\s+', ' ', ctx)
    print(f"  @{pos}: {ctx[:150]}")

# Find floor number patterns
print("\n=== Text patterns like 'X out of Y' or 'Xth floor' ===")
floor_ctx = [(m.start(), html[max(0,m.start()-80):m.end()+80]) for m in re.finditer(r'\d+\s*(?:out of|/)\s*\d+', html)]
for pos, ctx in floor_ctx[:10]:
    ctx = re.sub(r'<[^>]+>', ' ', ctx).strip()
    ctx = re.sub(r'\s+', ' ', ctx)
    print(f"  @{pos}: {ctx[:120]}")

# Find where "Balconies" text is in context
print("\n=== Context around 'Balcon' ===")
balc_ctx = [(m.start(), html[max(0,m.start()-200):m.end()+50]) for m in re.finditer(r'[Bb]alcon', html)]
for pos, ctx in balc_ctx[:5]:
    ctx = re.sub(r'<[^>]+>', ' | ', ctx).strip()
    ctx = re.sub(r'\s+', ' ', ctx)
    print(f"  @{pos}: {ctx[:200]}")

# Check for specific "Rent" section with actual rental listings
print("\n=== Searching for rent listing containers ===")
rent_sections = re.findall(r'class="([^"]*(?:rent|listing|available)[^"]*)"', html, re.IGNORECASE)
unique_rent = list(set(rent_sections))[:20]
for c in sorted(unique_rent):
    print(f"  {c}")
