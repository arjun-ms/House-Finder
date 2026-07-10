"""Parse the dumped SRP cards to identify how to extract data directly from the SRP."""
import sys, re
sys.stdout.reconfigure(encoding='utf-8')

with open("tests/fixtures/srp_cards.html", "r", encoding="utf-8") as f:
    html = f.read()

cards = html.split("<!-- CARD")
print(f"Total cards found: {len(cards)-1}")

for i, card in enumerate(cards[1:4]): # Look at first 3 cards
    print(f"\n{'='*80}")
    print(f"CARD {i}")
    
    # Extract title
    title_match = re.search(r'class="mb-srp__card--title"[^>]*>(.*?)</h2>', card, re.DOTALL)
    title = re.sub(r'<[^>]+>', '', title_match.group(1)).strip() if title_match else "N/A"
    print(f"Title: {title}")
    
    # Extract price
    price_match = re.search(r'class="mb-srp__card__price--amount"[^>]*>(.*?)</div>', card, re.DOTALL)
    price = re.sub(r'<[^>]+>', '', price_match.group(1)).strip() if price_match else "N/A"
    print(f"Price: {price}")
    
    # Extract summary info (floor, age, furnishing, etc)
    summary_items = re.findall(r'class="mb-srp__card__summary--label"[^>]*>(.*?)</div>\s*<div class="mb-srp__card__summary--value"[^>]*>(.*?)</div>', card, re.DOTALL | re.IGNORECASE)
    
    print("Summary Data:")
    for label, value in summary_items:
        label = re.sub(r'<[^>]+>', '', label).strip()
        value = re.sub(r'<[^>]+>', '', value).strip()
        print(f"  {label}: {value}")
        
    # Check if there is balcony info in summary
    balcony_match = re.search(r'Balconies?</div>\s*<div[^>]*>(.*?)</div>', card, re.IGNORECASE)
    if balcony_match:
        b = re.sub(r'<[^>]+>', '', balcony_match.group(1)).strip()
        print(f"  Balcony: {b}")

    # Check for listing URL
    url_match = re.search(r'href="([^"]+)"', card)
    if url_match:
        print(f"URL: {url_match.group(1)}")
