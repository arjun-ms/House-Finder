"""Parse the captured detail page HTML to find the correct selectors for floor, age, price, balcony."""
import re, sys
sys.stdout.reconfigure(encoding='utf-8')

with open("tests/fixtures/detail_page_pdpid.html", "r", encoding="utf-8") as f:
    html = f.read()

print(f"Total HTML length: {len(html)} chars")

# Find elements with class containing key terms
patterns = {
    "price/Price": r'class="([^"]*(?:price|Price)[^"]*)"[^>]*>([^<]{0,120})',
    "rent/Rent": r'class="([^"]*(?:rent|Rent)[^"]*)"[^>]*>([^<]{0,120})',
    "floor/Floor": r'class="([^"]*(?:floor|Floor)[^"]*)"[^>]*>([^<]{0,120})',
    "age/Age": r'class="([^"]*(?:age|Age)[^"]*)"[^>]*>([^<]{0,120})',
    "balcon": r'class="([^"]*(?:balcon|Balcon)[^"]*)"[^>]*>([^<]{0,120})',
    "dtls": r'class="([^"]*dtls[^"]*)"[^>]*>([^<]{0,120})',
    "summary": r'class="([^"]*summary[^"]*)"[^>]*>([^<]{0,120})',
    "ldp": r'class="([^"]*mb-ldp[^"]*)"[^>]*>([^<]{0,120})',
}

for label, pattern in patterns.items():
    matches = re.findall(pattern, html)
    if matches:
        print(f"\n=== {label}: {len(matches)} matches ===")
        seen = set()
        for cls, text in matches[:20]:
            text = text.strip()
            if text and cls not in seen:
                seen.add(cls)
                print(f"  class='{cls}' -> '{text[:80]}'")

# Also search for raw text patterns that contain floor/age info
print("\n=== Raw text containing 'Floor' ===")
floor_matches = re.findall(r'>([^<]*[Ff]loor[^<]*)<', html)
for m in floor_matches[:15]:
    m = m.strip()
    if m and len(m) < 100:
        print(f"  '{m}'")

print("\n=== Raw text containing 'Year' or 'Age' ===")
age_matches = re.findall(r'>([^<]*(?:[Yy]ear|[Aa]ge|[Oo]ld|[Nn]ew)[^<]*)<', html)
for m in age_matches[:15]:
    m = m.strip()
    if m and len(m) < 100:
        print(f"  '{m}'")

print("\n=== Raw text containing 'Balcon' ===")
balc_matches = re.findall(r'>([^<]*[Bb]alcon[^<]*)<', html)
for m in balc_matches[:15]:
    m = m.strip()
    if m and len(m) < 100:
        print(f"  '{m}'")

print("\n=== Raw text containing rent amount patterns (number + /month or per month) ===")
rent_matches = re.findall(r'>([^<]*(?:/month|per month|monthly|rent)[^<]*)<', html, re.IGNORECASE)
for m in rent_matches[:15]:
    m = m.strip()
    if m and len(m) < 100:
        print(f"  '{m}'")
