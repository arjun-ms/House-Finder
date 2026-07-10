"""
Browser Agent - Playwright automation for MagicBricks property scraping.

Handles:
1. Launching headed browser with video recording
2. Navigating to MagicBricks and interacting with search form
3. Collecting listing URLs from search results (with pagination)
4. Scraping property details from individual listing pages
"""

import asyncio
import random
import re
from playwright.async_api import async_playwright, Page, Browser, BrowserContext

import config
from agent_tools import AgentTools


async def random_delay():
    """Add a random delay between actions to appear human-like."""
    delay = random.uniform(config.MIN_DELAY, config.MAX_DELAY)
    await asyncio.sleep(delay)


async def dismiss_popups(page: Page):
    """Attempt to close any popups, modals, or cookie banners."""
    popup_selectors = [
        # Common close button patterns on MagicBricks
        "button.close",
        ".modal .close",
        "#closeButton",
        ".popup-close",
        "[data-dismiss='modal']",
        ".notification-close",
        # Cookie consent
        "#cookie-accept",
        ".cookie-close",
        # Generic overlay close
        ".overlay-close",
        "button[aria-label='Close']",
        "button[aria-label='close']",
        # MagicBricks specific
        ".mb-close",
        ".cross-icon",
        "#closeLoginPopup",
        ".login-popup__close",
    ]
    # Press Escape to close the dropdown if needed
    try:
        await page.keyboard.press("Escape")
    except:
        pass
    for selector in popup_selectors:
        try:
            element = page.locator(selector).first
            if await element.is_visible(timeout=500):
                await element.evaluate('el => el.click()')
                await asyncio.sleep(0.5)
        except Exception:
            continue


async def launch_browser():
    """Launch a headed Chromium browser with video recording."""
    playwright = await async_playwright().start()

    browser = await playwright.chromium.launch(
        headless=not config.HEADED,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
        ],
    )

    context_options = {
        "viewport": {
            "width": config.VIEWPORT_WIDTH,
            "height": config.VIEWPORT_HEIGHT,
        },
        "user_agent": config.USER_AGENT,
    }

    if config.RECORD_VIDEO:
        context_options["record_video_dir"] = config.VIDEO_DIR
        context_options["record_video_size"] = {
            "width": config.VIEWPORT_WIDTH,
            "height": config.VIEWPORT_HEIGHT,
        }

    context = await browser.new_context(**context_options)
    page = await context.new_page()
    
    async def handle_new_page(new_page: Page):
        try:
            opener = await new_page.opener()
            if opener is not None:
                print(f"[!] Blocked unexpected popup tab (Likely an Ad).")
                await new_page.close()
        except Exception:
            pass
                
    context.on("page", lambda p: asyncio.create_task(handle_new_page(p)))
    
    async def block_ads(route):
        url = route.request.url
        if "home-interior" in url.lower() or "hp_toolsandadvicesection" in url.lower():
            print(f"[!] Blocked background network request to ad/banner: {url}")
            await route.abort()
        else:
            await route.continue_()
            
    await context.route("**/*", block_ads)
    
    page.set_default_timeout(config.PAGE_LOAD_TIMEOUT)
    page.on("dialog", lambda dialog: asyncio.create_task(dialog.accept()))

    return playwright, browser, context, page


async def navigate_to_magicbricks(page: Page, tools: AgentTools = None):
    """Navigate to MagicBricks homepage and dismiss any initial popups."""
    print("[*] Navigating to MagicBricks...")
    await page.goto(config.MAGICBRICKS_URL, wait_until="domcontentloaded")
    await asyncio.sleep(3)  # Let page fully render
    await dismiss_popups(page)
    if tools:
        await tools.inspect_step("navigate", "body")
    print("[*] MagicBricks homepage loaded.")


async def select_rent_tab(page: Page, tools: AgentTools = None):
    """Click the Rent tab to switch to rental search mode."""
    print("[*] Selecting 'Rent' tab...")
    
    # Usually Magicbricks uses id 'tabRENT' for the Rent tab
    try:
        rent_tab = page.locator("#tabRENT")
        await rent_tab.wait_for(state="attached", timeout=5000)
        await rent_tab.evaluate("el => el.click()")
        # Wait for the categoryType hidden input to change to 'R', or wait a moment
        await page.wait_for_function('document.getElementById("categoryType") && document.getElementById("categoryType").value === "R"', timeout=3000)
        print("[*] 'Rent' tab selected successfully.")
        return
    except Exception as e:
        print(f"[!] Primary rent tab selection failed: {e}. Trying fallback...")
        
    rent_selectors = [
        ".mb-search__tab__item:has-text('Rent')",
        "div[data-url*='rent']",
        ".mb-search__tab .mb-search__tab__item:has-text('Rent')"
    ]
    
    for selector in rent_selectors:
        try:
            element = page.locator(selector).first
            if await element.is_visible(timeout=2000):
                await element.evaluate("el => el.click()")
                await asyncio.sleep(1)
                print(f"[*] 'Rent' tab selected via fallback selector: {selector}")
                return
        except Exception:
            continue
    print("[!] Could not find Rent tab, proceeding anyway (may already be on Rent).")
    if tools:
        await tools.inspect_step("rent_tab", "body")


def deduplicate_properties(properties: list[dict]) -> list[dict]:
    """Remove duplicate properties by listing_url, keeping the first occurrence."""
    seen_urls = set()
    unique = []
    for prop in properties:
        url = prop.get("listing_url", "")
        if url and url in seen_urls:
            continue
        if url:
            seen_urls.add(url)
        unique.append(prop)
    return unique


async def get_dynamic_locations(page: Page, keyword: str, max_locations: int = 3) -> list[str]:

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


async def apply_bhk_filter(page: Page, tools: AgentTools = None):
    """Select 2 BHK exclusively from the BHK filter options."""
    print("[*] Applying BHK filter (2 BHK only)...")
    
    # Click the property type dropdown to open it first
    try:
        prop_dropdown = page.locator(".mb-search__property .mb-search__title").first
        if await prop_dropdown.is_visible(timeout=2000):
            await prop_dropdown.evaluate('el => el.click()')
            await asyncio.sleep(0.5)
    except Exception:
        pass

    try:
        # MagicBricks checks 2 and 3 BHK by default. We need to uncheck the wrong ones.
        # Loop through indices 0 to 5 (1 BHK to 5+ BHK)
        for i in range(6):
            checkbox = page.locator(f"input#bhkFlatHouse_{i}")
            label = page.locator(f"label[for='bhkFlatHouse_{i}']")
            
            if await checkbox.count() > 0 and await label.is_visible(timeout=500):
                is_checked = await checkbox.is_checked()
                if i == 1:  # Index 1 is 2 BHK
                    if not is_checked:
                        await label.evaluate('el => el.click()')
                        await asyncio.sleep(0.2)
                else:       # Other BHKs
                    if is_checked:
                        await label.evaluate('el => el.click()')
                        await asyncio.sleep(0.2)
        
        print("[*] 2 BHK filter applied exclusively.")
        if tools:
            await tools.inspect_step("bhk_filter", ".mb-search__property")
        return
    except Exception as e:
        print(f"[!] Could not apply BHK filter, proceeding without it. Error: {e}")


async def apply_budget_filter(page: Page, tools: AgentTools = None):
    """Set the budget range filter (50k-60k)."""
    print(f"[*] Applying budget filter ({config.MIN_BUDGET}-{config.MAX_BUDGET})...")

    # Click the budget dropdown to open it first
    try:
        budget_dropdown = page.locator(".mb-search__budget .mb-search__title").first
        if await budget_dropdown.is_visible(timeout=2000):
            await budget_dropdown.evaluate('el => el.click()')
            await asyncio.sleep(0.5)
    except Exception:
        pass

    # Try to find and interact with budget input fields
    min_selectors = [
        "#budgetMin",
        "#minBudget",
        "input[placeholder*='Min Price']",
        "input[placeholder*='Min']",
        ".min-budget input",
    ]

    max_selectors = [
        "#budgetMax",
        "#maxBudget",
        "input[placeholder*='Max Price']",
        "input[placeholder*='Max']",
        ".max-budget input",
    ]

    # Try min budget
    for selector in min_selectors:
        try:
            element = page.locator(selector).first
            if await element.is_visible(timeout=2000):
                await element.evaluate('el => el.click()')
                await asyncio.sleep(0.3)
                await element.fill(str(config.MIN_BUDGET))
                print(f"[*] Min budget set to {config.MIN_BUDGET}")
                break
        except Exception:
            continue

    await asyncio.sleep(0.5)

    # Try max budget
    for selector in max_selectors:
        try:
            element = page.locator(selector).first
            if await element.is_visible(timeout=2000):
                await element.evaluate('el => el.click()')
                await asyncio.sleep(0.3)
                await element.fill(str(config.MAX_BUDGET))
                print(f"[*] Max budget set to {config.MAX_BUDGET}")
                break
        except Exception:
            continue

    # Click outside to close the budget dropdown (so it doesn't cover the search button)
    try:
        await page.mouse.click(0, 0)
        await asyncio.sleep(0.5)
    except Exception:
        pass

    print("[*] Budget filter applied.")
    if tools:
        await tools.inspect_step("budget_filter", ".mb-search__budget")


async def apply_more_filters(page: Page, floor_option: str, tools: AgentTools = None):
    """Click 'More Filters' and select a specific Floor option."""
    print(f"[*] Applying 'More Filters' (Floor {floor_option})...")
    
    more_filters_selectors = [
        ".mb-search__more-filter",
        ".mb-search__filter-more",
        "div.mb-search__filter-more",
        "div.more-filter",
        "xpath=//div[contains(@class, 'more-filter')]",
        "xpath=//*[contains(text(), 'More Filters')]",
        "xpath=//*[contains(., 'More Filters') and contains(@class, 'search')]"
    ]
    
    clicked_more = False
    for sel in more_filters_selectors:
        try:
            el = page.locator(sel).first
            if await el.is_visible(timeout=1000):
                await el.evaluate('el => el.click()')
                clicked_more = True
                break
        except Exception:
            continue
            
    if not clicked_more:
        try:
            el = page.locator("text=/More Filters/i").first
            if await el.is_visible(timeout=2000):
                await el.evaluate('el => el.click()')
                clicked_more = True
        except Exception:
            pass

    if not clicked_more:
        print("[!] Could not find 'More Filters' button, skipping...")
        return
        
    await asyncio.sleep(1)
    
    try:
        floor_tab = page.locator("text='Floor'").first
        if await floor_tab.is_visible(timeout=2000):
            await floor_tab.evaluate('el => el.click()')
            await asyncio.sleep(0.5)
    except Exception as e:
        print(f"[!] Could not select 'Floor' tab: {e}")
        
    # Click floor pill
    try:
        pill = page.locator(f"text='{floor_option}'").first
        if await pill.is_visible(timeout=1000):
            await pill.evaluate('el => el.click()')
            await asyncio.sleep(0.3)
            print(f"[*] Selected floor option: {floor_option}")
    except Exception as e:
        print(f"[!] Could not select floor '{floor_option}': {e}")

            
    # Apply button (sometimes "View X Properties")
    # Apply button (sometimes "View X Properties" or "Apply")
    apply_btn_selectors = [
        "text=/View .* Properties/i",
        "text='Apply'",
        "text='View Properties'",
        "div.mb-search__filter-btn",
        ".mb-search__filter-action button",
        "xpath=//div[contains(@class, 'filter')]//button[contains(text(), 'View')]",
        "xpath=//div[contains(@class, 'filter')]//button[contains(text(), 'Apply')]"
    ]
    
    applied = False
    for sel in apply_btn_selectors:
        try:
            apply_btn = page.locator(sel).first
            if await apply_btn.is_visible(timeout=1000):
                await apply_btn.evaluate('el => el.click()')
                print(f"[*] Applied More Filters using selector: {sel}")
                await asyncio.sleep(2)
                applied = True
                break
        except Exception:
            continue
            
    if not applied:
        print("[!] Could not find the Apply button in More Filters. Pressing Escape...")
        await page.keyboard.press("Escape")
        await asyncio.sleep(1)
        
    if tools:
        await tools.inspect_step("more_filters", "body")



async def click_search(page: Page, tools: AgentTools = None):
    """Click the search button to execute the search."""
    print("[*] Clicking Search button...")
    search_btn_selectors = [
        ".mb-search__btn",
        "div[onclick*='homepageSearchFormURL']",
        "#searchBtn",
        ".mb-home__search-btn"
    ]
    clicked = False
    for selector in search_btn_selectors:
        try:
            element = page.locator(selector).first
            if await element.is_visible(timeout=3000):
                await element.evaluate("el => el.click()")
                print("[*] Search initiated.")
                await page.wait_for_load_state("domcontentloaded")
                await asyncio.sleep(3)
                clicked = True
                break
        except Exception:
            continue
    
    if not clicked:
        # Fallback: press Enter
        print("[!] Could not find search button, pressing Enter...")
        await page.keyboard.press("Enter")
        await asyncio.sleep(3)

    # Post-search URL verification and correction
    current_url = page.url
    if "for-sale" in current_url or "buy" in current_url.lower():
        print("[!] Detected incorrect redirection to 'buy/sale' properties. Correcting URL to 'rent'...")
        fixed_url = current_url.replace("for-sale", "for-rent").replace("category=S", "category=R")
        if "buy" in fixed_url.lower() and "rent" not in fixed_url.lower():
            fixed_url = fixed_url.replace("buy", "rent").replace("Buy", "Rent")
        await page.goto(fixed_url, wait_until="domcontentloaded")
        await asyncio.sleep(3)
    elif "home-interior" in current_url:
        print("[!] Detected incorrect redirection to home interiors. Attempting direct navigation to rental search...")
        # Construct fallback direct URL for Whitefield, Bangalore, 2BHK, 50k-60k
        direct_url = f"https://www.magicbricks.com/property-for-rent/residential-real-estate?bedroom=2&proptype=Multistorey-Apartment,Builder-Floor-Apartment,Penthouse,Studio-Apartment&locality={target_location}&budgetMin={config.MIN_BUDGET}&budgetMax={config.MAX_BUDGET}"
        await page.goto(direct_url, wait_until="domcontentloaded")
        await asyncio.sleep(3)



async def collect_properties_from_srp(page: Page) -> list[dict]:
    """
    Collect property data directly from search results cards.
    Paginates until MAX_LISTINGS_TO_SCRAPE properties are collected.
    """
    print(f"\\n[*] Collecting properties directly from SRP (target: {config.MAX_LISTINGS_TO_SCRAPE})...")
    all_properties = []
    seen_urls = set()
    page_num = 1

    for page_num in range(1, 10): 
        print(f"[*] Scanning search results page {page_num}...")
        await dismiss_popups(page)
        await asyncio.sleep(2)

        try:
            cards = await page.locator(".mb-srp__card").all()
            print(f"[*] Found {len(cards)} property cards on page {page_num}.")
            
            for card in cards:
                if len(all_properties) >= config.MAX_LISTINGS_TO_SCRAPE:
                    break
                    
                try:
                    card_html = await card.inner_html(timeout=1000)
                    prop_data = parse_srp_card_html(card_html)
                    
                    if prop_data.get("listing_url"):
                        url = prop_data["listing_url"]
                        if url not in seen_urls:
                            seen_urls.add(url)
                            all_properties.append(prop_data)
                            print(f"  [DEBUG] -> Parsed from SRP: {prop_data['property_name']} | ₹{prop_data['price']}")
                except Exception as e:
                    pass
                    
        except Exception as e:
            print(f"[!] Error collecting cards: {e}")

        if len(cards) == 0:
            print(f"[!] No property cards found on page {page_num}. Stopping pagination.")
            break

        print(f"[*] Total properties collected so far: {len(all_properties)}")

        if len(all_properties) >= config.MAX_LISTINGS_TO_SCRAPE:
            break

        next_clicked = False
        print("[*] Scrolling down to trigger infinite load...")
        
        for _ in range(5):
            await page.evaluate("window.scrollBy(0, 3000)")
            await asyncio.sleep(1.5)
            
        new_cards = await page.locator(".mb-srp__card").all()
        if len(new_cards) > len(cards):
            next_clicked = True
            page_num += 1
            print(f"[*] Loaded more items via scroll (Total cards now: {len(new_cards)}).")

        if not next_clicked:
            print("[!] No more properties loaded. Done collecting.")
            break

    return all_properties





def parse_number(text: str) -> int | float | None:
    """Extract a number from text like '12th Floor', '3 Years', '1,200 sq.ft.'"""
    if not text:
        return None
    # Remove commas and extra spaces
    text = text.replace(",", "").strip()
    # Find all actual numbers (int or float) avoiding stray periods
    numbers = re.findall(r"\d+(?:\.\d+)?", text)
    if numbers:
        try:
            val = float(numbers[0])
            return int(val) if val == int(val) else val
        except ValueError:
            return None
    return None


def parse_srp_card_html(card_html: str) -> dict:
    """Parse property data directly from an SRP card HTML string."""
    property_data = {
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
        "listing_url": None,
    }
    
    # URL
    url_match = re.search(r'href="([^"]+)"', card_html)
    if url_match:
        url = url_match.group(1)
        if url.startswith("/"):
            url = config.MAGICBRICKS_URL + url
        property_data["listing_url"] = url

    # Property Name / Title
    title_match = re.search(r'class="[^"]*title[^"]*"[^>]*>(.*?)</h2>', card_html, re.DOTALL | re.IGNORECASE)
    if title_match:
        title = re.sub(r'<[^>]+>', '', title_match.group(1)).strip()
        property_data["property_name"] = title
        if " in " in title:
            property_data["location"] = title.split(" in ")[-1].strip()
        if "BHK" in title:
            bhk_match = re.search(r'(\d+)\s*BHK', title)
            if bhk_match:
                property_data["bhk_config"] = f"{bhk_match.group(1)} BHK"
    
    # Rent Price
    price_match = re.search(r'class="[^"]*price[^"]*"[^>]*>(.*?)</div>', card_html, re.DOTALL | re.IGNORECASE)
    if price_match:
        price_text = re.sub(r'<[^>]+>', '', price_match.group(1)).strip()
        parsed = parse_price(price_text)
        if parsed: property_data["price"] = parsed

    # Summary data (Floor, Area, Furnishing, Balcony)
    summary_items = re.findall(r'class="[^"]*summary--label[^"]*"[^>]*>(.*?)</div>\s*<div class="[^"]*summary--value[^"]*"[^>]*>(.*?)</div>', card_html, re.DOTALL | re.IGNORECASE)
    
    for label, value in summary_items:
        label = re.sub(r'<[^>]+>', '', label).strip().lower()
        value = re.sub(r'<[^>]+>', '', value).strip()
        
        if "floor" in label:
            floor_match = re.search(r'(\d+)\s*(?:out of|/|of)\s*(\d+)', value)
            if floor_match:
                property_data["floor_number"] = int(floor_match.group(1))
                property_data["total_floors"] = int(floor_match.group(2))
            else:
                num = parse_number(value)
                if num:
                    property_data["floor_number"] = int(num)
        
        elif "area" in label:
            property_data["built_up_area"] = value
            
        elif "furnish" in label:
            property_data["furnishing_status"] = value
            
        elif "balcon" in label:
            num = parse_number(value)
            if num:
                property_data["balcony_count"] = int(num)
                
    # Also check if balcony is mentioned in its own label
    balcony_match = re.search(r'Balconies?</div>\s*<div[^>]*>(.*?)</div>', card_html, re.IGNORECASE)
    if balcony_match and property_data["balcony_count"] is None:
        b = re.sub(r'<[^>]+>', '', balcony_match.group(1)).strip()
        num = parse_number(b)
        if num:
            property_data["balcony_count"] = int(num)

    return property_data


def parse_price(text: str) -> int | None:
    if not text: return None
    text = text.replace(",", "").strip()
    rent_match = re.search(r"Rent[^\d]*([\d.]+)\s*(Cr|Lac|Lakh|K|k)?", text, re.IGNORECASE)
    match = rent_match if rent_match else re.search(r"([\d.]+)\s*(Cr|Lac|Lakh|K|k)?", text, re.IGNORECASE)
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

async def scrape_property_detail(context, prop: dict) -> dict | None:
    """
    Navigate to a property detail page and extract all data fields.
    Returns a dict with property data, or None on failure.
    """
    url = prop.get("listing_url")
    if not url: return prop
    property_data = prop.copy()

    page = await context.new_page()
    page.on("dialog", lambda dialog: asyncio.create_task(dialog.accept()))
    try:
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
                    else:
                        property_data["price"] = price_text[:20]  # truncate garbage
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
        # MagicBricks often shows details in key-value pairs
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
            if "floor" in text_lower and property_data["floor_number"] is None:
                # Patterns: "Floor: 12 out of 20", "12th Floor", "Floor 12/20"
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
                if property_data["property_age"] is None:
                    num = parse_number(text)
                    if num is not None:
                        property_data["property_age"] = 2026 - num if num > 1900 else num

            # Balcony
            elif "balcon" in text_lower:
                if property_data["balcony_count"] is None:
                    num = parse_number(text)
                    property_data["balcony_count"] = int(num) if num else 1

            # BHK Config
            elif "bhk" in text_lower:
                if property_data["bhk_config"] is None:
                    property_data["bhk_config"] = text.strip()

            # Area
            elif any(kw in text_lower for kw in ["sq", "area", "sqft", "sq.ft", "carpet", "built"]):
                if property_data["built_up_area"] is None:
                    property_data["built_up_area"] = text.strip()

            # Furnishing
            elif any(kw in text_lower for kw in ["furnish", "unfurnish", "semi"]):
                if property_data["furnishing_status"] is None:
                    property_data["furnishing_status"] = text.strip()

            # Deposit
            elif any(kw in text_lower for kw in ["deposit", "security"]):
                if property_data["deposit_amount"] is None:
                    property_data["deposit_amount"] = text.strip()

        # --- Amenities ---
        amenity_selectors = [
            ".mb-ldp__amenities li",
            ".amenities li",
            "[class*='amenity'] li",
            "[class*='Amenity'] li",
            ".feature-list li",
        ]
        for sel in amenity_selectors:
            try:
                items = page.locator(sel)
                count = await items.count()
                if count > 0:
                    amenities = []
                    for i in range(min(count, 20)):  # Cap at 20 amenities
                        text = await items.nth(i).text_content()
                        if text and text.strip():
                            amenities.append(text.strip())
                    property_data["amenities"] = amenities
                    break
            except Exception:
                continue

        # --- Builder / Society ---
        builder_selectors = [
            "[class*='builder']",
            "[class*='Builder']",
            "[class*='society']",
            "[class*='Society']",
            "[class*='developer']",
            ".mb-ldp__builder",
        ]
        for sel in builder_selectors:
            try:
                el = page.locator(sel).first
                if await el.is_visible(timeout=1000):
                    property_data["builder_society"] = (await el.text_content()).strip()
                    break
            except Exception:
                continue

        print(f"[{index}/{total}] Scraped: {property_data.get('property_name') or 'Unknown'}... OK")
        return property_data

    except Exception as e:
        print(f"[{index}/{total}] FAILED ({type(e).__name__}: {str(e)[:100]}), skipping")
        return None
    finally:
        try:
            # page.close() can sometimes hang during cancellation, blocking wait_for
            asyncio.create_task(page.close())
        except Exception:
            pass



async def run_browser_agent() -> list[dict]:
    """
    Full browser automation pipeline looping over specific localities.
    """
    from playwright.async_api import async_playwright
    
    properties = []
    failed_count = 0
    
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            headless=not config.HEADED,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
        )
        context = await browser.new_context(
            viewport={"width": config.VIEWPORT_WIDTH, "height": config.VIEWPORT_HEIGHT},
            user_agent=config.USER_AGENT,
            record_video_dir=config.VIDEO_DIR if config.RECORD_VIDEO else None
        )
        page = await context.new_page()
        
        async def block_ads(route):
            url = route.request.url
            if "home-interior" in url.lower() or "hp_toolsandadvicesection" in url.lower():
                await route.abort()
            else:
                await route.continue_()
                
        await context.route("**/*", block_ads)
        
        # Dynamically discover matching localities from the dropdown
        locations_to_test = await get_dynamic_locations(page, config.SEARCH_KEYWORD, max_locations=config.MAX_LOCATIONS_TO_SELECT)
        
        for loc in locations_to_test:
            print(f"\\n{'='*60}\\nScraping Location: {loc}\\n{'='*60}")
            page = await context.new_page()
            
            async def handle_new_page(new_page):
                try:
                    opener = await new_page.opener()
                    if opener is not None:
                        await new_page.close()
                except:
                    pass
            context.on("page", lambda p: asyncio.create_task(handle_new_page(p)))
            page.on("dialog", lambda dialog: asyncio.create_task(dialog.accept()))
            
            tools = AgentTools(page)
            
            try:
                await navigate_to_magicbricks(page, tools)
                await random_delay()
                await select_rent_tab(page, tools)
                await random_delay()
                
                # Fill the specific location
                target_location = loc
                config.MAX_LOCATIONS_TO_SELECT = 1
                await fill_location(page, loc, tools)
                await random_delay()
                
                await apply_bhk_filter(page, tools)
                await random_delay()
                
                await apply_budget_filter(page, tools)
                await random_delay()
                
                await click_search(page, tools)
                await random_delay()
                
                # Wait for search results
                await page.wait_for_selector(".mb-srp__list", state="attached", timeout=config.PAGE_LOAD_TIMEOUT)
                await asyncio.sleep(2)
                
                # Apply exact Owner filter via XPath
                print("[*] Attempting to click 'Owners' filter via XPath...")
                try:
                    posted_by = page.locator("xpath=/html/body/div/div/div/div[2]/div[1]/div/div[2]/div[5]/div")
                    if await posted_by.count() > 0:
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
                            print("[!] Could not find Owners label")
                    else:
                        print("[!] Could not find 'Posted By' filter via XPath")
                except Exception as e:
                    print(f"[!] Error clicking Owner filter: {e}")
                
                # Collect Properties directly from Search Results Page
                props = await collect_properties_from_srp(page)
                
                if not props:
                    print(f"[!] No properties collected for {loc}")
                    await page.close()
                    continue
                    
                print(f"[*] Collected {len(props)} properties for {loc}!")
                properties.extend(props)

                    
            except Exception as e:
                print(f"[!] Critical error in location loop {loc}: {e}")
            finally:
                await page.close()
                
        print(f"\\n{'='*60}\\nALL LOCATIONS SCRAPED\\n  Succeeded: {len(properties)}\\n  Failed: {failed_count}\\n{'='*60}\\n")
        
        # Deduplicate properties from overlapping location searches
        before_dedup = len(properties)
        properties = deduplicate_properties(properties)
        if before_dedup != len(properties):
            print(f"[*] Deduplication: {before_dedup} -> {len(properties)} unique properties")
        
        return properties


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
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=config.DETAIL_PAGE_TIMEOUT)
        except Exception as load_e:
            print(f"[!] Goto timeout or error ({load_e}), continuing to scrape whatever loaded...")
        
        await asyncio.sleep(3)
        await dismiss_popups(page)

        # --- Property Name ---
        if property_data.get("property_name") is None:
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
        if property_data.get("price") is None:
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
        browser = await p.chromium.launch(headless=not config.HEADED)
        context = await browser.new_context(viewport={'width': 1280, 'height': 800})
        
        for i, prop in enumerate(props):
            url = prop.get("listing_url")
            print(f"  [{i+1}/{len(props)}] Deep scraping: {str(prop.get('property_name', url))[:40]}...")
            data = await scrape_property_detail(context, prop)
            if data:
                results.append(data)
                
        await browser.close()
    return results
