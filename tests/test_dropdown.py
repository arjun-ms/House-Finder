import asyncio
from playwright.async_api import async_playwright

async def test_dropdown():
    locations = [
        "Whitefield",
        "Whitefield Hoskote Road",
        "Whitefield Main Road"
    ]
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=["--disable-blink-features=AutomationControlled"])
        context = await browser.new_context(viewport={"width": 1280, "height": 800})
        
        for loc in locations:
            print(f"\n{'='*40}\nTesting Location Dropdown: {loc}\n{'='*40}")
            page = await context.new_page()
            
            await page.goto("https://www.magicbricks.com/", timeout=60000)
            await asyncio.sleep(2)
            
            input_box = page.locator("#keyword")
            await input_box.fill("")
            await asyncio.sleep(0.5)
            
            print(f"[*] Typing exact keyword: '{loc}'")
            await input_box.type(loc, delay=100)
            await asyncio.sleep(3)
            
            # Wait for suggest dropdown
            try:
                await page.wait_for_selector("#serachSuggest", state="visible", timeout=5000)
                items = page.locator("#serachSuggest .mb-search__auto-suggest__item")
                count = await items.count()
                print(f"[*] Found {count} items in dropdown.")
                
                clicked = False
                for i in range(count):
                    el = items.nth(i)
                    text = await el.text_content()
                    onclick = await el.get_attribute("onclick") or ""
                    
                    if text:
                        text = text.strip()
                        # We want a locality match that starts with our location
                        if loc.lower() in text.lower() and "locality" in onclick.lower():
                            print(f"[*] MATCH! Clicking dropdown item: '{text}'")
                            await el.click()
                            clicked = True
                            break
                            
                if not clicked:
                    print(f"[!] Could not find any exact locality match for '{loc}'")
                    # Fallback
                    await page.keyboard.press("Enter")
                    
            except Exception as e:
                print(f"[!] Dropdown error: {e}")
                
            await asyncio.sleep(3)
            await page.close()
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_dropdown())
