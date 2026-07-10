import asyncio
from playwright.async_api import async_playwright

async def test_swap_location():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=["--disable-blink-features=AutomationControlled"])
        context = await browser.new_context(viewport={"width": 1280, "height": 800})
        page = await context.new_page()
        
        # Go to homepage and search for Whitefield
        await page.goto("https://www.magicbricks.com/")
        await asyncio.sleep(2)
        
        input_box = page.locator("#keyword")
        await input_box.fill("")
        await input_box.type("Whitefield", delay=100)
        await asyncio.sleep(3)
        
        # Extract suggestions
        items = page.locator("#serachSuggest .mb-search__auto-suggest__item")
        count = await items.count()
        locations = []
        for i in range(min(count, 3)):
            text = await items.nth(i).text_content()
            onclick = await items.nth(i).get_attribute("onclick") or ""
            if "locality" in onclick.lower():
                locations.append(text.strip())
                
        print(f"Extracted locations: {locations}")
        
        # Click first one and search
        if locations:
            await items.nth(0).click()
            await asyncio.sleep(1)
            
            # Click search
            search_btn = page.locator(".mb-search__btn")
            await search_btn.click()
            await asyncio.sleep(5)
            
            # Now we are on results page. Try to swap location.
            # Look for the search bar on the results page
            print("On results page. Attempting to swap location...")
            
            # Usually it's an input with placeholder "Add more locations..." or similar
            # Let's dump the DOM or take a screenshot
            await page.screenshot(path="results_page_searchbar.png")
            
            html = await page.content()
            with open("results_page.html", "w", encoding="utf-8") as f:
                f.write(html)
                
            print("Saved screenshot and DOM to inspect how to swap locations.")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_swap_location())
