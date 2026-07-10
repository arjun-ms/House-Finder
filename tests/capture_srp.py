"""Capture the HTML of search result cards from a real MagicBricks SRP."""
import asyncio, sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.async_api import async_playwright

async def capture_srp():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        context = await browser.new_context(viewport={"width": 1280, "height": 800})
        page = await context.new_page()

        # Go directly to a rent search results URL
        url = "https://www.magicbricks.com/property-for-rent/residential-real-estate?bedroom=2&proptype=Multistorey-Apartment,Builder-Floor-Apartment,Penthouse,Studio-Apartment&budgetmin=30000&budgetmax=40000&Locality=Whitefield&cityName=Bangalore"
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(5)

        # Save full SRP HTML
        html = await page.content()
        with open("tests/fixtures/srp_page.html", "w", encoding="utf-8") as f:
            f.write(html)
        print(f"Saved SRP HTML ({len(html)} chars)")

        # Extract individual listing cards
        cards = await page.locator(".mb-srp__card").all()
        print(f"\nFound {len(cards)} .mb-srp__card elements")

        for i, card in enumerate(cards[:3]):
            card_html = await card.inner_html()
            print(f"\n{'='*60}")
            print(f"CARD {i+1} (raw text):")
            text = await card.text_content()
            print(text.strip()[:500] if text else "EMPTY")
            
            # Look for specific data points
            print(f"\nCARD {i+1} subselectors:")
            
            # Property name
            name_el = card.locator("[class*='title'], h2, [class*='name']").first
            try:
                name = await name_el.text_content()
                print(f"  Name: {name.strip()[:80]}")
            except:
                print("  Name: NOT FOUND")

            # Price
            price_el = card.locator("[class*='price']").first
            try:
                price = await price_el.text_content()
                print(f"  Price: {price.strip()[:80]}")
            except:
                print("  Price: NOT FOUND")

            # Floor
            try:
                floor_els = await card.locator("[class*='floor'], [class*='Floor']").all()
                for fel in floor_els:
                    ft = await fel.text_content()
                    fc = await fel.get_attribute("class")
                    print(f"  Floor element: class='{fc}' text='{ft.strip()[:60]}'")
            except:
                print("  Floor: NOT FOUND")

            # Summary list items
            try:
                summary_items = await card.locator("[class*='summary'] [class*='item'], .mb-srp__card__summary__list--item").all()
                print(f"  Summary items: {len(summary_items)}")
                for j, item in enumerate(summary_items[:10]):
                    it = await item.text_content()
                    ic = await item.get_attribute("class")
                    print(f"    [{j}] class='{ic}' text='{it.strip()[:80]}'")
            except:
                print("  Summary: NOT FOUND")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(capture_srp())
