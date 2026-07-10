import re

def update_browser_agent():
    with open("browser_agent.py", "r", encoding="utf-8") as f:
        code = f.read()

    # 1. Update run_browser_agent to loop over locations
    new_run = '''
async def run_browser_agent() -> list[dict]:
    """
    Full browser automation pipeline looping over specific Whitefield localities.
    """
    from playwright.async_api import async_playwright
    
    properties = []
    failed_count = 0
    
    locations_to_test = [
        "Whitefield",
        "Whitefield Hoskote Road",
        "Whitefield Main Road"
    ]
    
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
        
        async def block_ads(route):
            url = route.request.url
            if "home-interior" in url.lower() or "hp_toolsandadvicesection" in url.lower():
                await route.abort()
            else:
                await route.continue_()
                
        await context.route("**/*", block_ads)
        
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
                config.SEARCH_KEYWORD = loc
                config.MAX_LOCATIONS_TO_SELECT = 1
                await fill_location(page, tools)
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
                            done_btn = page.locator("div", has_text="Done").last
                            await done_btn.click()
                            print("[*] Clicked 'Owners' and 'Done'!")
                            await asyncio.sleep(5)
                        else:
                            print("[!] Could not find Owners label")
                    else:
                        print("[!] Could not find 'Posted By' filter via XPath")
                except Exception as e:
                    print(f"[!] Error clicking Owner filter: {e}")
                
                # Collect URLs
                urls = await collect_listing_urls(page)
                
                if not urls:
                    print(f"[!] No URLs for {loc}")
                    await page.close()
                    continue
                    
                print(f"[*] Scraping {len(urls)} properties for {loc}...")
                for i, url in enumerate(urls, 1):
                    try:
                        property_data = await asyncio.wait_for(
                            scrape_property_detail(context, url, i, len(urls)), 
                            timeout=45.0
                        )
                    except Exception as e:
                        print(f"[{i}/{len(urls)}] FAILED: {e}")
                        property_data = None
                        
                    if property_data:
                        properties.append(property_data)
                    else:
                        failed_count += 1
                    await random_delay()
                    
            except Exception as e:
                print(f"[!] Critical error in location loop {loc}: {e}")
            finally:
                await page.close()
                
        print(f"\\n{'='*60}\\nALL LOCATIONS SCRAPED\\n  Succeeded: {len(properties)}\\n  Failed: {failed_count}\\n{'='*60}\\n")
        return properties
'''
    # Replace run_browser_agent
    code = re.sub(r'async def run_browser_agent\(\) -> list\[dict\]:.*?(?=\n\n\n|$)', new_run, code, flags=re.DOTALL)
    
    # 2. Fix fill_location to click search properly (avoiding Enter submitting form prematurely if needed, though we already fixed it)
    # 3. Fix collect_listing_urls timeout error (using await .all() instead of nth(i))
    new_collect = '''
async def collect_listing_urls(page: Page) -> list[str]:
    """
    Collect property listing URLs from search results.
    Paginates until MAX_LISTINGS_TO_SCRAPE URLs are collected.
    """
    print(f"\\n[*] Collecting listing URLs (target: {config.MAX_LISTINGS_TO_SCRAPE})...")
    all_urls = []
    page_num = 1

    for page_num in range(1, 10): 
        print(f"[*] Scanning search results page {page_num}...")
        await dismiss_popups(page)
        await asyncio.sleep(2)

        found_urls = []
        try:
            all_links = await page.locator(".mb-srp__list a[href], .mb-srp__card a[href], a[data-type='property']").all()
            print(f"[*] Found {len(all_links)} raw links on page {page_num}.")
            
            for link in all_links:
                try:
                    href = await link.get_attribute("href", timeout=500)
                    if not href:
                        continue
                    href_lower = href.lower()
                    is_valid = True 
                    
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
                except:
                    pass
        except Exception as e:
            print(f"[!] Error collecting links: {e}")

        if len(all_links) == 0:
            print(f"[!] No property cards found on page {page_num}. Stopping pagination.")
            break

        for u in found_urls:
            if u not in all_urls and len(all_urls) < config.MAX_LISTINGS_TO_SCRAPE:
                all_urls.append(u)
                
        print(f"[*] Total URLs collected so far: {len(all_urls)}")

        if len(all_urls) >= config.MAX_LISTINGS_TO_SCRAPE:
            break

        next_clicked = False
        print("[*] Scrolling down to trigger infinite load...")
        
        for _ in range(5):
            await page.evaluate("window.scrollBy(0, 3000)")
            await asyncio.sleep(1.5)
            
        new_links = await page.locator(".mb-srp__list a[href], .mb-srp__card a[href], a[data-type='property'], a[href*='/property-details/']").all()
        new_count = len(new_links)
        
        if new_count > len(all_links):
            next_clicked = True
            page_num += 1
            print(f"[*] Loaded more items via scroll (Total raw links now: {new_count}).")

        if not next_clicked:
            print("[!] No more properties loaded. Done collecting URLs.")
            break

    all_urls = all_urls[: config.MAX_LISTINGS_TO_SCRAPE]
    print(f"\\n[*] Collected {len(all_urls)} listing URLs total.")
    return all_urls
'''
    code = re.sub(r'async def collect_listing_urls\(page: Page\) -> list\[str\]:.*?(?=\n\n\ndef parse_number)', new_collect, code, flags=re.DOTALL)
    
    with open("browser_agent.py", "w", encoding="utf-8") as f:
        f.write(code)
    print("browser_agent.py updated successfully.")

if __name__ == "__main__":
    update_browser_agent()
