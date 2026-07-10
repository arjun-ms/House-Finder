import re

def update():
    with open("browser_agent.py", "r", encoding="utf-8") as f:
        code = f.read()

    new_func = '''async def fill_location(page: Page, tools: AgentTools = None):
    """Type exact keyword in the search box, wait for suggest dropdown, and click the correct item."""
    print(f"[*] Typing '{config.SEARCH_KEYWORD}' in search box...")

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
    
    print(f"[*] Typing exact keyword: '{config.SEARCH_KEYWORD}'")
    await input_element.type(config.SEARCH_KEYWORD, delay=100)
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
                if config.SEARCH_KEYWORD.lower() in text.lower() and "locality" in onclick.lower():
                    print(f"[*] MATCH! Clicking dropdown item: '{text}'")
                    await el.click()
                    clicked = True
                    break
                    
        if not clicked:
            print(f"[!] Could not find any exact locality match for '{config.SEARCH_KEYWORD}'")
            await page.keyboard.press("Enter")
            
    except Exception as e:
        print(f"[!] Dropdown error: {e}")
        await page.keyboard.press("Enter")
        
    await asyncio.sleep(2)
'''

    code = re.sub(r'async def fill_location\(page: Page, tools: AgentTools = None\):.*?(?=\n\nasync def apply_bhk_filter)', new_func, code, flags=re.DOTALL)
    
    with open("browser_agent.py", "w", encoding="utf-8") as f:
        f.write(code)
    print("Fixed fill_location logic")

if __name__ == "__main__":
    update()
