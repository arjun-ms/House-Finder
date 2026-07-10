import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://www.magicbricks.com/")
        
        # We need to type something to make the suggest box appear
        await page.fill("#keyword", "Whitefield")
        await asyncio.sleep(3)
        
        # Test the faulty selector
        option_selector = "#serachSuggest, .mb-search__auto-suggest, .mb-search__auto-suggest__list, .sugg-list, .auto-suggest, .pac-container"
        
        # What does this locator match?
        locator1 = f"{option_selector} >> text=Whitefield"
        
        count = await page.locator(locator1).count()
        print(f"Count for locator1: {count}")
        if count > 0:
            first_el = page.locator(locator1).first
            html = await first_el.evaluate("el => el.outerHTML")
            print(f"First element matched by locator1: {html[:200]}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
