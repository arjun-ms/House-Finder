import asyncio
from playwright.async_api import async_playwright

async def test_swap_results_fixed():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=["--disable-blink-features=AutomationControlled"])
        context = await browser.new_context(viewport={"width": 1280, "height": 800})
        page = await context.new_page()
        
        await page.goto("https://www.magicbricks.com/")
        await asyncio.sleep(2)
        
        # 1. First search for Whitefield
        input_box = page.locator("#keyword")
        await input_box.fill("")
        await input_box.type("Whitefield", delay=100)
        await asyncio.sleep(3)
        
        items = page.locator("#serachSuggest .mb-search__auto-suggest__item")
        count = await items.count()
        locations = []
        for i in range(min(count, 3)):
            text = await items.nth(i).text_content()
            onclick = await items.nth(i).get_attribute("onclick") or ""
            if text and "locality" in onclick.lower():
                locations.append(text.strip())
                
        print(f"[*] Found localities: {locations}")
        
        if locations:
            await items.nth(0).click()
            await asyncio.sleep(1)
            await page.locator(".mb-search__btn").click()
            await asyncio.sleep(5)
            
            print(f"[*] Results page 1 loaded: {page.url}")
            
            if len(locations) > 1:
                next_loc = locations[1]
                print(f"[*] Swapping to: {next_loc}")
                
                # Close the original pill
                print("[*] Clicking X on existing pill...")
                close_btn = page.locator(".auto-suggest__tag-close").first
                if await close_btn.is_visible():
                    await close_btn.click()
                    await asyncio.sleep(1)
                
                # Type new location
                add_more = page.locator(".topCityLocality")
                await add_more.focus()
                await add_more.type(next_loc, delay=100)
                await asyncio.sleep(3)
                
                # Wait for dropdown on results page
                sugg = page.locator(".mb-search__auto-suggest__item")
                count = await sugg.count()
                for i in range(count):
                    text = await sugg.nth(i).text_content()
                    if text and next_loc.lower() in text.lower():
                        print(f"[*] Clicking suggestion: {text.strip()}")
                        await sugg.nth(i).click()
                        break
                        
                await asyncio.sleep(1)
                
                # Click Done to trigger search
                done_btn = page.locator(".filter__component__cta-done").first
                if await done_btn.is_visible():
                    print("[*] Clicking Done button...")
                    await done_btn.click()
                else:
                    await page.keyboard.press("Enter")
                    
                await asyncio.sleep(5)
                print(f"[*] Results page 2 loaded: {page.url}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_swap_results_fixed())
