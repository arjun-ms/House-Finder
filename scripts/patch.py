code = '''
async def scrape_property_detail(context, prop: dict) -> dict | None:
    """Scrape detailed information from a property's dedicated page, merging with existing data."""
    import re
    url = prop.get("listing_url")
    if not url: return prop
    
    property_data = prop.copy()
    page = await context.new_page()
    import asyncio
    page.on("dialog", lambda dialog: asyncio.create_task(dialog.accept()))
    try:
        import config
        await page.goto(url, wait_until="domcontentloaded", timeout=config.DETAIL_PAGE_TIMEOUT)
        await asyncio.sleep(2)
        await dismiss_popups(page)

        # --- Property Name ---
        name_selectors = [
            "h1",
            ".mb-ldp__title",
            ".property-name",
            ".prop-name",
            "[class*='title'] h1",
            "[class*='Title'] h1",
        ]
        for sel in name_selectors:
            try:
                el = page.locator(sel).first
                if await el.is_visible(timeout=1000):
                    val = (await el.text_content()).strip()
                    if val: property_data["property_name"] = val
                    break
            except Exception:
                continue

        # --- Price ---
        price_selectors = [
            "[class*='price']",
            "[class*='Price']",
            ".mb-ldp__price",
            ".propPrice",
            "#price",
        ]
        
        for sel in price_selectors:
            try:
                el = page.locator(sel).first
                if await el.is_visible(timeout=1000):
                    price_text = (await el.text_content()).strip()
                    parsed = parse_price(price_text)
                    if parsed:
                        property_data["price"] = parsed
                    elif price_text:
                        property_data["price"] = price_text[:20]
                    break
            except Exception:
                continue

        # --- Location ---
        location_selectors = [
            "[class*='locality']",
            "[class*='Locality']",
            "[class*='address']",
            "[class*='Address']",
            ".mb-ldp__locality",
            ".prop-location",
        ]
        for sel in location_selectors:
            try:
                el = page.locator(sel).first
                if await el.is_visible(timeout=1000):
                    val = (await el.text_content()).strip()
                    if val: property_data["location"] = val
                    break
            except Exception:
                continue

        # --- Extract from detail/info table rows ---
        detail_selectors = [
            ".mb-srp__card:nth-child(1) .mb-srp__card__summary__list--item",
            ".mb-srp__card__summary__list--item",
            ".mb-ldp__dtls li",
            ".mb-ldp__more--dtl li",
            ".propInfoList li",
            ".detail-list li",
            ".prop-dtl li",
            "table.propInfo tr",
            "[class*='detail'] li",
            "[class*='Detail'] li",
            "[class*='info'] li",
        ]

        detail_texts = []
        for sel in detail_selectors:
            try:
                items = page.locator(sel)
                count = await items.count()
                if count > 0:
                    for i in range(count):
                        text = await items.nth(i).text_content()
                        if text:
                            detail_texts.append(text.strip())
                    break
            except Exception:
                continue

        print(f"DETAIL TEXTS FOUND: {detail_texts}")

        # Parse detail texts for specific fields
        for text in detail_texts:
            text_lower = text.lower()

            # Floor
            if "floor" in text_lower and not property_data.get("floor_number"):
                floor_match = re.search(r"(\d+)\s*(?:out of|/|of)\s*(\d+)", text)
                if floor_match:
                    property_data["floor_number"] = int(floor_match.group(1))
                    property_data["total_floors"] = int(floor_match.group(2))
                else:
                    num = parse_number(text)
                    if num:
                        property_data["floor_number"] = int(num)

            # Property Age
            elif any(kw in text_lower for kw in ["age", "year", "old", "possession"]):
                if not property_data.get("property_age"):
                    num = parse_number(text)
                    if num is not None:
                        property_data["property_age"] = 2026 - num if num > 1900 else num

            # Balcony
            elif "balcon" in text_lower:
                if not property_data.get("balcony_count"):
                    num = parse_number(text)
                    if num is not None:
                        property_data["balcony_count"] = num

        return property_data

    except Exception as e:
        print(f"[!] Error scraping detail page {url}: {e}")
        return prop
    finally:
        await page.close()


async def scrape_details_for_urls(props: list[dict]) -> list[dict]:
    """Deep scrape multiple properties and merge."""
    results = []
    from playwright.async_api import async_playwright
    import config
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=config.HEADLESS)
        context = await browser.new_context(viewport={'width': 1280, 'height': 800})
        
        for i, prop in enumerate(props):
            url = prop.get("listing_url")
            print(f"  [{i+1}/{len(props)}] Deep scraping: {str(prop.get('property_name', url))[:40]}...")
            data = await scrape_property_detail(context, prop)
            if data:
                results.append(data)
                
        await browser.close()
    return results
'''

with open('browser_agent.py', 'a', encoding='utf-8') as f:
    f.write(code)
