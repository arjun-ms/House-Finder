"""Capture the DOM of a real MagicBricks property detail page for test fixture creation."""
import asyncio
from playwright.async_api import async_playwright

async def capture_detail_page():
    url = "https://www.magicbricks.com/desai-radiant-itpl-bangalore-pdpid-4d4235303838353335"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(5)
        
        # Get full HTML
        html = await page.content()
        with open("tests/fixtures/detail_page_pdpid.html", "w", encoding="utf-8") as f:
            f.write(html)
        print(f"[*] Saved full HTML ({len(html)} chars)")
        
        # Also get a single listing page (non-pdpid)
        url2 = "https://www.magicbricks.com/property-for-rent/2-bhk-flat-for-rent-in-whitefield-bangalore-pdpid-4d4234373335383531"
        try:
            await page.goto(url2, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(5)
            html2 = await page.content()
            with open("tests/fixtures/detail_page_single.html", "w", encoding="utf-8") as f:
                f.write(html2)
            print(f"[*] Saved single listing HTML ({len(html2)} chars)")
        except Exception as e:
            print(f"[!] Could not fetch single listing: {e}")
        
        # Now let's extract what selectors actually contain on the pdpid page
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(3)
        
        # Check what h1 contains
        h1 = await page.locator("h1").first.text_content()
        print(f"\n[h1]: {h1}")
        
        # Check price elements
        price_els = await page.locator("[class*='price'], [class*='Price']").all()
        print(f"\n[price elements]: {len(price_els)} found")
        for i, el in enumerate(price_els[:5]):
            text = await el.text_content()
            cls = await el.get_attribute("class")
            print(f"  {i}: class='{cls}' text='{text.strip()[:80]}'")
        
        # Check for rent-specific elements
        rent_els = await page.locator("[class*='rent'], [class*='Rent']").all()
        print(f"\n[rent elements]: {len(rent_els)} found")
        for i, el in enumerate(rent_els[:5]):
            text = await el.text_content()
            cls = await el.get_attribute("class")
            print(f"  {i}: class='{cls}' text='{text.strip()[:80]}'")
        
        # Check detail/info selectors
        detail_selectors = [
            ".mb-ldp__dtls li",
            ".mb-ldp__more--dtl li", 
            ".mb-ldp__dtls__body__summary--item",
            ".mb-ldp__dtls__body__list--item",
            "[class*='dtls'] li",
            "[class*='summary'] li",
            "[class*='floor']",
            "[class*='Floor']",
            "[class*='age']",
            "[class*='Age']",
            "[class*='balcon']",
            "[class*='Balcon']",
        ]
        
        for sel in detail_selectors:
            items = await page.locator(sel).all()
            if items:
                print(f"\n[{sel}]: {len(items)} elements")
                for i, el in enumerate(items[:8]):
                    text = await el.text_content()
                    cls = await el.get_attribute("class") or ""
                    print(f"  {i}: class='{cls[:40]}' text='{text.strip()[:80]}'")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(capture_detail_page())
