import pytest
import asyncio
from agents.browser_agent import parse_srp_card_html
from playwright.async_api import async_playwright

pytestmark = pytest.mark.asyncio

async def test_srp_card_extraction():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        page = await context.new_page()
        
        await page.goto("https://www.magicbricks.com/property-for-rent/residential-real-estate?bedroom=2&proptype=multistorey-apartment,builder-floor-apartment,penthouse,studio-apartment,service-apartment,residential-house,villa&locality=Whitefield&cityname=bangalore", wait_until="domcontentloaded")
        await asyncio.sleep(5)
        
        # Get the first property card HTML
        cards = page.locator(".mb-srp__card")
        count = await cards.count()
        print(f"\n[*] Found {count} property cards on SRP.")
        
        if count > 0:
            html = await cards.nth(0).inner_html()
            print("\n[*] First Card HTML Length:", len(html))
            
            # Now run it through our parser
            data = parse_srp_card_html(html)
            print("\n[*] Extracted Data:")
            for k, v in data.items():
                print(f"  {k}: {v}")
                
        await browser.close()
