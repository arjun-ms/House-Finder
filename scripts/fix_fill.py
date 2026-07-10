import re

def update():
    with open("browser_agent.py", "r", encoding="utf-8") as f:
        code = f.read()

    new_func = '''async def fill_location(page: Page, tools: AgentTools = None):
    """Type exact keyword in the search box, clear existing pills, and press Enter to select."""
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
    
    await page.keyboard.press("Enter")
    print("[*] Pressed Enter to select autocomplete item.")
    await asyncio.sleep(2)
'''

    code = re.sub(r'async def fill_location\(page: Page, tools: AgentTools = None\):.*?(?=\n\nasync def apply_bhk_filter)', new_func, code, flags=re.DOTALL)
    
    with open("browser_agent.py", "w", encoding="utf-8") as f:
        f.write(code)

if __name__ == "__main__":
    update()
