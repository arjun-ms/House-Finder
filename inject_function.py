import re

def main():
    with open('browser_agent.py', 'r', encoding='utf-8') as f:
        code = f.read()

    dynamic_extract = '''async def get_dynamic_locations(page: Page, keyword: str, max_locations: int = 3) -> list[str]:
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
        locations = [keyword]
        
    if not locations:
        locations = [keyword]
        
    print(f"[*] Dynamically found {len(locations)} locations: {locations}")
    return locations

async def fill_location'''

    code = code.replace('async def fill_location', dynamic_extract)

    with open('browser_agent.py', 'w', encoding='utf-8') as f:
        f.write(code)
    print('Injected get_dynamic_locations')

if __name__ == "__main__":
    main()
