import asyncio
from playwright.async_api import async_playwright

async def analyze_workflow():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width": 1280, "height": 800})
        page = await context.new_page()
        
        print("1. Going to MagicBricks")
        await page.goto("https://www.magicbricks.com/", timeout=60000)
        await page.screenshot(path="step1_home.png")
        
        print("2. Clicking Rent")
        rent_tab = page.locator(".mb-search__tab__item", has_text="Rent")
        if await rent_tab.count() > 0:
            await rent_tab.first.click()
        await asyncio.sleep(1)
        await page.screenshot(path="step2_rent.png")
        
        print("3. Typing Whitefield")
        await page.locator("#keyword").fill("")
        await page.locator("#keyword").type("Whitefield", delay=100)
        await asyncio.sleep(3)
        await page.screenshot(path="step3_dropdown.png")
        
        print("4. Clicking dropdown and searching")
        # Click the first Location item
        await page.locator(".mb-search__auto-suggest__item", has_text="Whitefield, Bangalore").first.click()
        await asyncio.sleep(1)
        
        # Click Search button
        await page.locator(".mb-search__btn").click()
        
        try:
            await page.wait_for_selector(".mb-srp__list", timeout=20000)
            await asyncio.sleep(5)
            await page.screenshot(path="step4_search_results.png")
        except Exception as e:
            print("Failed to load search results:", e)
            await page.screenshot(path="step4_error.png")
        
        print("5. Looking for Owner Filter")
        owner_html = ""
        # Let's extract any filter bar elements
        filter_bars = page.locator(".mb-filter")
        if await filter_bars.count() > 0:
            owner_html = await filter_bars.first.inner_html()
            
        with open("search_dom.html", "w", encoding="utf-8") as f:
            f.write(await page.content())
            
        print("Workflow complete.")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(analyze_workflow())
