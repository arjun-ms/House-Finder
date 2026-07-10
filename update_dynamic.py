import re

def update():
    with open("browser_agent.py", "r", encoding="utf-8") as f:
        code = f.read()

    # 1. We need a function to extract dynamic locations
    dynamic_extract = '''async def get_dynamic_locations(page: Page, keyword: str, max_locations: int = 3) -> list[str]:
    """Type the keyword into the homepage search, wait for the dropdown, and extract the top matching localities."""
    print(f"[*] Extracting dynamic locations for '{keyword}'...")
    await page.goto("https://www.magicbricks.com/", timeout=60000)
    await asyncio.sleep(2)
    
    input_box = page.locator("#keyword")
    await input_box.fill("")
    await input_box.type(keyword, delay=100)
    await asyncio.sleep(3)
    
    locations = []
    try:
        await page.wait_for_selector("#serachSuggest", state="visible", timeout=5000)
        items = page.locator("#serachSuggest .mb-search__auto-suggest__item")
        count = await items.count()
        
        for i in range(count):
            text = await items.nth(i).text_content()
            onclick = await items.nth(i).get_attribute("onclick") or ""
            if text and "locality" in onclick.lower():
                locations.append(text.strip())
                if len(locations) >= max_locations:
                    break
    except Exception as e:
        print(f"[!] Error extracting locations: {e}")
        locations = [keyword] # Fallback to just the keyword
        
    print(f"[*] Dynamically found {len(locations)} locations: {locations}")
    return locations

async def fill_location(page: Page, target_location: str, tools: AgentTools = None):
    """Type exact keyword in the search box, wait for suggest dropdown, and click the correct item."""
    print(f"[*] Typing '{target_location}' in search box...")

    search_selectors = [
        "#keyword", "#suggester-input", "input[placeholder*='locality']",
        "input[placeholder*='Search']", "input[placeholder*='search']",
        ".search-input input", ".sugg_input", "#autoSuggest",
        "input[name='keyword']", ".mb-home__search input", "input[type='text']",
    ]

    input_element = None
    for selector in search_selectors:
        try:
            element = page.locator(selector).first
            if await element.is_visible(timeout=2000):
                input_element = element
                break
        except:
            continue

    if not input_element:
        raise Exception("Could not find the search input field.")

    await input_element.focus()
    await asyncio.sleep(0.5)
    
    print("[*] Clearing existing location pills...")
    for _ in range(5):
        await page.keyboard.press("Backspace")
        await asyncio.sleep(0.2)
        
    await input_element.fill("")
    await asyncio.sleep(0.3)
    
    print(f"[*] Typing exact keyword: '{target_location}'")
    await input_element.type(target_location, delay=100)
    await asyncio.sleep(3)
    
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
                if target_location.lower() in text.lower() and "locality" in onclick.lower():
                    print(f"[*] MATCH! Clicking dropdown item: '{text}'")
                    await el.click()
                    clicked = True
                    break
                    
        if not clicked:
            print(f"[!] Could not find any exact locality match for '{target_location}'")
            await page.keyboard.press("Enter")
            
    except Exception as e:
        print(f"[!] Dropdown error: {e}")
        await page.keyboard.press("Enter")
        
    await asyncio.sleep(2)
'''

    # Replace fill_location and insert get_dynamic_locations
    code = re.sub(r'async def fill_location.*?asyncio\.sleep\(2\)\n', dynamic_extract, code, flags=re.DOTALL)
    
    # 2. Update run_browser_agent to use dynamic extraction instead of hardcoded list
    run_func_match = re.search(r'async def run_browser_agent.*?locations_to_test = \["Whitefield", "Whitefield Hoskote Road", "Whitefield Main Road"\]', code, flags=re.DOTALL)
    if run_func_match:
        replacement = '''async def run_browser_agent(max_listings: int = 10):
    print("="*60)
    print(f"[STEP 1/4] Launching browser agent...")
    print("-" * 60)
    
    all_properties = []

    async with async_playwright() as p:
        # Launch browser once
        browser = await p.chromium.launch(
            headless=config.HEADLESS,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        # 1. DYNAMICALLY EXTRACT LOCATIONS
        locations_to_test = await get_dynamic_locations(page, config.SEARCH_KEYWORD, max_locations=config.MAX_LOCATIONS_TO_SELECT)
        '''
        
        code = code.replace(run_func_match.group(0), replacement)
        
        # 3. Update the call to fill_location inside the loop
        code = code.replace('await fill_location(page, tools)', 'await fill_location(page, loc, tools)')
        
        with open("browser_agent.py", "w", encoding="utf-8") as f:
            f.write(code)
        print("Updated browser_agent.py with dynamic location extraction!")
    else:
        print("Could not find run_browser_agent to update.")

if __name__ == "__main__":
    update()
