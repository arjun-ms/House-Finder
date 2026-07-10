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


async def fill_location(page: Page, tools: AgentTools = None):
    """Type partial keyword in the search box, clear existing pills, and select dropdown option."""
    print(f"[*] Typing '{config.SEARCH_KEYWORD}' in search box...")

    # Try multiple possible search input selectors
    search_selectors = [
        "#keyword",
        "#suggester-input",
        "input[placeholder*='locality']",
        "input[placeholder*='Search']",
        "input[placeholder*='search']",
        ".search-input input",
        ".sugg_input",
        "#autoSuggest",
        "input[name='keyword']",
        ".mb-home__search input",
        "input[type='text']",
    ]

    input_element = None
    for selector in search_selectors:
        try:
            element = page.locator(selector).first
            if await element.is_visible(timeout=2000):
                input_element = element
                print(f"[*] Found search input with selector: {selector}")
                break
        except Exception:
            continue

    if not input_element:
        raise Exception("Could not find the search input field on MagicBricks.")

    # Click the input to focus
    await input_element.focus()
    await asyncio.sleep(0.5)
    
    # Press backspace multiple times to clear any pre-selected location "pills" (e.g., Bangalore)
    print("[*] Clearing existing location pills...")
    for _ in range(5):
        await page.keyboard.press("Backspace")
        await asyncio.sleep(0.2)
        
    await input_element.fill("")
    await asyncio.sleep(0.3)
    
    # Type partial keyword (e.g. "Whitefiel" if config is "Whitefield")
    partial_keyword = config.SEARCH_KEYWORD[:-1] if len(config.SEARCH_KEYWORD) > 4 else config.SEARCH_KEYWORD
    print(f"[*] Typing partial keyword: '{partial_keyword}'")
    await input_element.type(partial_keyword, delay=100)
    await asyncio.sleep(3)  # Wait longer for dropdown suggestions to appear and render

    # Look for the dropdown option containing the keyword
    print("[*] Looking for dropdown suggestions...")
    
    selected_count = 0
    try:
        # Wait for the suggest dropdown container to appear
        await page.wait_for_selector("#serachSuggest", state="visible", timeout=5000)
        
        # Get all suggestion items (the actual clickable divs)
        items = page.locator("#serachSuggest .mb-search__auto-suggest__item")
        await asyncio.sleep(0.5)
        count = await items.count()
        print(f"[*] Found {count} dropdown suggestion items")
        
        # Collect only LOCATION items (onclick contains "locality"), skip Projects
        location_items = []
        for i in range(count):
            try:
                el = items.nth(i)
                onclick = await el.get_attribute("onclick", timeout=1000)
                text = await el.text_content(timeout=1000)
                if onclick and text:
                    text = text.strip()
                    is_locality = "locality" in onclick.lower()
                    has_keyword = config.SEARCH_KEYWORD.lower() in text.lower()
                    has_city = config.CITY.lower() in text.lower()
                    print(f"[*]   Item {i}: '{text}' locality={is_locality} keyword={has_keyword} city={has_city}")
                    if is_locality and has_keyword and has_city:
                        location_items.append((i, text))
            except Exception:
                continue
        
        # Cap at MAX_LOCATIONS_TO_SELECT
        location_items = location_items[:config.MAX_LOCATIONS_TO_SELECT]
        print(f"[*] Will select {len(location_items)} locations: {[t for _, t in location_items]}")
        
        # Click each location item
        for idx, (item_index, text) in enumerate(location_items):
            try:
                # After clicking a previous item, the dropdown might close
                # Re-trigger it by clearing and retyping
                if idx > 0:
                    await input_element.click()
                    await asyncio.sleep(0.3)
                    await input_element.type(partial_keyword, delay=80)
                    await asyncio.sleep(3)
                    # Re-fetch the items since DOM may have refreshed
                    items = page.locator("#serachSuggest .mb-search__auto-suggest__item")
                
                # Find the right item by matching onclick for locality
                current_count = await items.count()
                clicked = False
                for j in range(current_count):
                    el = items.nth(j)
                    onclick = await el.get_attribute("onclick", timeout=1000)
                    el_text = await el.text_content(timeout=1000)
                    if onclick and el_text and "locality" in onclick.lower() and el_text.strip().lower() == text.lower():
                        await el.evaluate("el => el.click()")
                        selected_count += 1
                        clicked = True
                        print(f"[*] Selected location: '{text}'")
                        await asyncio.sleep(1)
                        break
                
                if not clicked:
                    print(f"[!] Could not re-find item: '{text}'")
            except Exception as e:
                print(f"[!] Failed to select '{text}': {e}")
                
    except Exception as e:
        print(f"[!] Error processing dropdown options: {e}")

    if selected_count == 0:
        # DO NOT press enter. Pressing enter searches default properties (e.g., Buy, Mumbai)
        raise Exception(f"Could not find any dropdown suggestion for '{config.SEARCH_KEYWORD}'. Aborting to prevent scraping wrong locations.")
    else:
        print(f"[*] Successfully selected {selected_count} locations.")
        if tools:
            await tools.inspect_step("location_selected", "#keyword_autoSuggestSelectedDiv")

    # Look for a "Done" button after selecting localities (sometimes required, sometimes not)
    done_selectors = [
        "button:has-text('Done')",
        "a:has-text('Done')",
        ".done-btn",
    ]
    for selector in done_selectors:
        try:
            element = page.locator(selector).first
            if await element.is_visible(timeout=1000):
                await element.evaluate('el => el.click()')
                await asyncio.sleep(0.5)
                print("[*] Clicked 'Done' button.")
                break
        except Exception:
            continue


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


async def apply_more_filters(page: Page, tools: AgentTools = None):
    """Click 'More Filters' and select Floor options (9-12, 13-16, 16+)."""
    print("[*] Applying 'More Filters' (Floor >= 9)...")
    
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
        
    # Click floor pills
    floor_options = ["9-12", "13-16", "16+"]
    for option in floor_options:
        try:
            pill = page.locator(f"text='{option}'").first
            if await pill.is_visible(timeout=1000):
                await pill.evaluate('el => el.click()')
                await asyncio.sleep(0.3)
                print(f"[*] Selected floor option: {option}")
        except Exception as e:
            print(f"[!] Could not select floor '{option}': {e}")
            
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
        direct_url = f"https://www.magicbricks.com/property-for-rent/residential-real-estate?bedroom=2&proptype=Multistorey-Apartment,Builder-Floor-Apartment,Penthouse,Studio-Apartment&locality={config.SEARCH_KEYWORD}&budgetMin={config.MIN_BUDGET}&budgetMax={config.MAX_BUDGET}"
        await page.goto(direct_url, wait_until="domcontentloaded")
        await asyncio.sleep(3)


async def collect_listing_urls(page: Page) -> list[str]:
    """
    Collect property listing URLs from search results.
    Paginates until MAX_LISTINGS_TO_SCRAPE URLs are collected.
    """
    print(f"\n[*] Collecting listing URLs (target: {config.MAX_LISTINGS_TO_SCRAPE})...")
    all_urls: list[str] = []
    page_num = 1

    while len(all_urls) < config.MAX_LISTINGS_TO_SCRAPE:
        print(f"[*] Scanning search results page {page_num}...")
        await dismiss_popups(page)
        await asyncio.sleep(2)

        # Grab all links on the page, but filter them strictly
        found_urls = []
        try:
            # First, try to get links from actual property cards if possible
            all_links = page.locator(".mb-srp__list a[href], .mb-srp__card a[href], a[data-type='property'], a[href*='/property-details/']")
            count = await all_links.count()
            print(f"[*] Found {count} raw links matching selectors on page {page_num}.")
            
            for i in range(count):
                href = await all_links.nth(i).get_attribute("href")
                if not href:
                    continue
                
                print(f"  [DEBUG] Raw href: {href}")
                    
                # Strict filtering to ignore banners, ads, and internal service links
                href_lower = href.lower()
                is_valid = False
                
                # Check for valid property patterns
                if "/property-details/" in href_lower or "propertydetail" in href_lower or "/property-for-" in href_lower or "pdpid-" in href_lower:
                    is_valid = True
                    
                # Exclude known bad patterns
                bad_patterns = [
                    "home-interior", "pppfs", "javascript:", "tel:", "mailto:", 
                    "banner", "login", "register", "contact-us"
                ]
                for bad in bad_patterns:
                    if bad in href_lower:
                        is_valid = False
                        break
                        
                if is_valid:
                    if href.startswith("/"):
                        href = config.MAGICBRICKS_URL + href
                    if href not in all_urls and "magicbricks.com" in href:
                        found_urls.append(href)
                        print(f"  [DEBUG] -> VALID: {href}")
                else:
                    print(f"  [DEBUG] -> FILTERED OUT")
        except Exception as e:
            print(f"[!] Error collecting links: {e}")

        if not found_urls:
            print(f"[!] No property URLs found on page {page_num}. Stopping pagination.")
            break

        # Append unique found_urls to all_urls
        for u in found_urls:
            if u not in all_urls and len(all_urls) < config.MAX_LISTINGS_TO_SCRAPE:
                all_urls.append(u)
                
        print(f"[*] Total URLs collected so far: {len(all_urls)}")

        if len(all_urls) >= config.MAX_LISTINGS_TO_SCRAPE:
            break

        # Try to go to next page
        next_clicked = False
        next_selectors = [
            "a:has-text('Next')",
            ".pagination__next",
            "a[aria-label='Next']",
            ".nextPage",
            "a.next",
            "li.next a",
        ]
        for selector in next_selectors:
            try:
                element = page.locator(selector).first
                if await element.is_visible(timeout=3000):
                    await element.evaluate('el => el.click()')
                    await page.wait_for_load_state("domcontentloaded")
                    await asyncio.sleep(3)
                    next_clicked = True
                    page_num += 1
                    print(f"[*] Navigated to page {page_num}.")
                    break
            except Exception:
                continue

        if not next_clicked:
            print("[!] No next page button found. Done collecting URLs.")
            break

    # Trim to max
    all_urls = all_urls[: config.MAX_LISTINGS_TO_SCRAPE]
    print(f"\n[*] Collected {len(all_urls)} listing URLs total.")
    return all_urls


def parse_number(text: str) -> int | float | None:
    """Extract a number from text like '12th Floor', '3 Years', '1,200 sq.ft.'"""
    if not text:
        return None
    # Remove commas and extra spaces
    text = text.replace(",", "").strip()
    # Find all numbers (int or float)
    numbers = re.findall(r"[\d.]+", text)
    if numbers:
        try:
            val = float(numbers[0])
            return int(val) if val == int(val) else val
        except ValueError:
            return None
    return None


async def scrape_property_detail(context, url: str, index: int, total: int) -> dict | None:
    """
    Navigate to a property detail page and extract all data fields.
    Returns a dict with property data, or None on failure.
    """
    from typing import Any
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
    }

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
                    property_data["property_name"] = (await el.text_content()).strip()
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
        
        def parse_price(text: str) -> int | None:
            if not text:
                return None
            text = text.replace(",", "").strip()
            
            # If "Rent" is in the text, try to extract the number after it
            rent_match = re.search(r"Rent[^\d]*([\d.]+)\s*(Cr|Lac|Lakh|K|k)?", text, re.IGNORECASE)
            if rent_match:
                match = rent_match
            else:
                # Match number and optional unit like Cr, Lac, K
                match = re.search(r"([\d.]+)\s*(Cr|Lac|Lakh|K|k)?", text, re.IGNORECASE)
                
            if match:
                try:
                    val = float(match.group(1))
                    unit = (match.group(2) or "").lower()
                    if "cr" in unit:
                        val *= 10000000
                    elif "lac" in unit or "lakh" in unit:
                        val *= 100000
                    elif "k" in unit:
                        val *= 1000
                    return int(val)
                except ValueError:
                    pass
            return None

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
                    property_data["location"] = (await el.text_content()).strip()
                    break
            except Exception:
                continue

        # --- Extract from detail/info table rows ---
        # MagicBricks often shows details in key-value pairs
        detail_selectors = [
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
                        property_data["property_age"] = num

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
    Full browser automation pipeline:
    1. Launch browser
    2. Navigate to MagicBricks
    3. Fill search form (Rent, Whitefield, 2BHK, budget)
    4. Collect listing URLs
    5. Scrape each property detail page
    6. Return list of property data dicts
    """
    from playwright.async_api import async_playwright
    
    async with async_playwright() as playwright:
        # Launch browser manually instead of using launch_browser to keep it in context
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
        
        # Block annoying redirects and popups
        async def block_ads(route):
            url = route.request.url
            if "home-interior" in url.lower() or "hp_toolsandadvicesection" in url.lower():
                print(f"[!] Blocked background network request to ad/banner: {url}")
                await route.abort()
            else:
                await route.continue_()
                
        await context.route("**/*", block_ads)
        
        async def handle_new_page(new_page):
            try:
                opener = await new_page.opener()
                if opener is not None:
                    print(f"[!] Blocked unexpected popup tab (Likely an Ad).")
                    await new_page.close()
            except Exception:
                pass
                    
        context.on("page", lambda p: asyncio.create_task(handle_new_page(p)))
        page.on("dialog", lambda dialog: asyncio.create_task(dialog.accept()))

        # Initialize agent inspection tools
        tools = AgentTools(page)

        try:
            # Step 1: Navigate and setup
            await navigate_to_magicbricks(page, tools)
            await random_delay()

            # Step 2: Select Rent tab
            await select_rent_tab(page, tools)
            await random_delay()

            # Step 3: Fill location
            await fill_location(page, tools)
            await random_delay()

            # Step 4: Apply BHK filter
            await apply_bhk_filter(page, tools)
            await random_delay()

            # Step 5: Apply budget filter
            await apply_budget_filter(page, tools)
            await random_delay()

            # Step 5.5: Execute search first (More Filters is only on the search results page)
            await click_search(page, tools)
            await tools.inspect_step("search_results", "body")
            await random_delay()

            # Step 6: Apply more filters (Floor) on the Search Results Page
            await apply_more_filters(page, tools)
            await random_delay()

            # Step 7: Collect listing URLs
            listing_urls = await collect_listing_urls(page)

            if not listing_urls:
                print("\n[!] No listing URLs found. The search may have returned no results.")
                await tools.inspect_step("no_results", "body")
                return []

            # Step 8: Scrape each property detail page
            print(f"\n{'='*60}")
            print(f"SCRAPING {len(listing_urls)} PROPERTY DETAIL PAGES")
            print(f"{'='*60}\n")

            properties = []
            failed_count = 0

            for i, url in enumerate(listing_urls, 1):
                try:
                    property_data = await asyncio.wait_for(
                        scrape_property_detail(context, url, i, len(listing_urls)), 
                        timeout=45.0
                    )
                except asyncio.TimeoutError:
                    print(f"[{i}/{len(listing_urls)}] FAILED (Hard Timeout: 45s), skipping")
                    property_data = None
                except Exception as e:
                    print(f"[{i}/{len(listing_urls)}] FAILED (Outer Error: {e}), skipping")
                    property_data = None
                    
                if property_data:
                    properties.append(property_data)
                else:
                    failed_count += 1
                await random_delay()

            print(f"\n{'='*60}")
            print(f"SCRAPING COMPLETE")
            print(f"  Succeeded: {len(properties)}")
            print(f"  Failed: {failed_count}")
            print(f"{'='*60}\n")

            return properties

        finally:
            # Context manager will cleanly close browser and playwright
            pass
