import re

def fix():
    with open("browser_agent.py", "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Move parse_price out
    parse_price_code = """
def parse_price(text: str) -> int | None:
    if not text: return None
    text = text.replace(",", "").strip()
    rent_match = re.search(r"Rent[^\\d]*([\\d.]+)\\s*(Cr|Lac|Lakh|K|k)?", text, re.IGNORECASE)
    match = rent_match if rent_match else re.search(r"([\\d.]+)\\s*(Cr|Lac|Lakh|K|k)?", text, re.IGNORECASE)
    if match:
        try:
            val = float(match.group(1))
            unit = (match.group(2) or "").lower()
            if "cr" in unit: val *= 10000000
            elif "lac" in unit or "lakh" in unit: val *= 100000
            elif "k" in unit: val *= 1000
            return int(val)
        except ValueError: pass
    return None
"""
    # Remove it from inside scrape_property_detail
    content = re.sub(r' +def parse_price\(text: str\) -> int \| None:.*?return None\n', '', content, flags=re.DOTALL)
    
    # Insert it before scrape_property_detail
    content = content.replace('async def scrape_property_detail(', parse_price_code + '\nasync def scrape_property_detail(')

    # 2. Update parse_srp_card_html
    old_price_srp = """    price_match = re.search(r'class="[^"]*price--amount[^"]*"[^>]*>(.*?)</div>', card_html, re.DOTALL | re.IGNORECASE)
    if price_match:
        price_text = re.sub(r'<[^>]+>', '', price_match.group(1)).strip()
        price_text = price_text.replace(",", "")
        num_match = re.search(r'(\\d+)', price_text)
        if num_match:
            property_data["price"] = int(num_match.group(1))"""
    new_price_srp = """    price_match = re.search(r'class="[^"]*price[^"]*"[^>]*>(.*?)</div>', card_html, re.DOTALL | re.IGNORECASE)
    if price_match:
        price_text = re.sub(r'<[^>]+>', '', price_match.group(1)).strip()
        parsed = parse_price(price_text)
        if parsed: property_data["price"] = parsed"""
    content = content.replace(old_price_srp, new_price_srp)

    # 3. Update scrape_property_detail signature and initialization
    old_sig = 'async def scrape_property_detail(context, url: str, index: int, total: int) -> dict | None:'
    new_sig = 'async def scrape_property_detail(context, prop: dict) -> dict | None:'
    content = content.replace(old_sig, new_sig)
    
    # Replace dict initialization
    old_init = """    from typing import Any
    property_data: dict[str, Any] = {
        "property_name": None,
        "price": None,
        "location": None,
        "bhk_config": None,
        "floor_number": None,
        "total_floors": None,
        "property_age": None,
        "balcony_count": None,
        "built_up_area": None,
        "furnishing_status": None,
        "amenities": [],
        "deposit_amount": None,
        "builder_society": None,
        "listing_url": url,
    }"""
    new_init = """    url = prop.get("listing_url")
    if not url: return prop
    property_data = prop.copy()"""
    content = content.replace(old_init, new_init)

    # Update deep scrape property name assignment
    content = content.replace(
        'property_data["property_name"] = (await el.text_content()).strip()',
        'val = (await el.text_content()).strip()\n                    if val: property_data["property_name"] = val'
    )

    # Update deep scrape location assignment
    content = content.replace(
        'property_data["location"] = (await el.text_content()).strip()',
        'val = (await el.text_content()).strip()\n                    if val: property_data["location"] = val'
    )

    # Update deep scrape age logic
    old_age = """                    num = parse_number(text)
                    if num is not None:
                        property_data["property_age"] = num"""
    new_age = """                    num = parse_number(text)
                    if num is not None:
                        property_data["property_age"] = 2026 - num if num > 1900 else num"""
    content = content.replace(old_age, new_age)

    # 4. Update scrape_details_for_urls
    content = content.replace(
        'async def scrape_details_for_urls(urls: list[str]) -> list[dict]:',
        'async def scrape_details_for_urls(props: list[dict]) -> list[dict]:'
    )
    content = content.replace(
        'for i, url in enumerate(urls):',
        'for i, prop in enumerate(props):\n            url = prop.get("listing_url")'
    )
    content = content.replace(
        'print(f"  [{i+1}/{len(urls)}] Scraped: {url[:60]}...")',
        'print(f"  [{i+1}/{len(props)}] Scraped: {prop.get(\'property_name\', url)[:40]}...")'
    )
    content = content.replace(
        'data = await scrape_property_detail(context, url, i, len(urls))',
        'data = await scrape_property_detail(context, prop)'
    )

    # 5. Fix Owner filter click logic
    old_owners = """                    if await posted_by.count() > 0:
                        await posted_by.first.click()
                        await asyncio.sleep(2)
                        owners_label = page.locator("label", has_text="Owners")
                        if await owners_label.count() > 0:
                            await owners_label.first.click()
                            await asyncio.sleep(1)
                            done_btn = page.locator("div", has_text="Done").last
                            await done_btn.click()
                            print("[*] Clicked 'Owners' and 'Done'!")
                            await asyncio.sleep(5)
                        else:
                            print("[!] Could not find Owners label")"""
    new_owners = """                    if await posted_by.count() > 0:
                        await posted_by.first.click()
                        await asyncio.sleep(2)
                        owners_label = page.locator("label", has_text="Owners")
                        if await owners_label.count() > 0:
                            await owners_label.first.click()
                            await asyncio.sleep(1)
                            
                            done_btn = page.locator("#body > div.top-filter > div > div.top-filter__item-all-filter > div:nth-child(5) > div > div.filter__component__drop-down > div.filter__component__cta-done")
                            if await done_btn.count() > 0:
                                await done_btn.first.click()
                            else:
                                await page.locator("div", has_text="Done").last.click()
                            
                            print("[*] Clicked 'Owners' and 'Done'!")
                            await asyncio.sleep(5)
                        else:
                            print("[!] Could not find Owners label")"""
    content = content.replace(old_owners, new_owners)

    with open("browser_agent.py", "w", encoding="utf-8") as f:
        f.write(content)
        
    print("Fixed!")

if __name__ == "__main__":
    fix()
