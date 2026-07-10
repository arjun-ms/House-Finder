import asyncio
from playwright.async_api import async_playwright

async def test_location_loop():
    locations_to_test = [
        "whitefield, bangalore",
        "whitefield hoskote road, bangalore"
    ]
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=["--disable-blink-features=AutomationControlled"])
        context = await browser.new_context(viewport={"width": 1280, "height": 800})
        
        for loc in locations_to_test:
            print(f"\n{'='*40}\nTesting Location: {loc}\n{'='*40}")
            page = await context.new_page()
            
            # 1. Navigate
            await page.goto("https://www.magicbricks.com/", timeout=60000)
            await asyncio.sleep(2)
            
            # 2. Select Rent
            rent_tab = page.locator(".mb-search__tab__item", has_text="Rent")
            if await rent_tab.count() > 0:
                await rent_tab.first.click()
                await asyncio.sleep(1)
            
            # Type keyword and pick ONE location
            input_box = page.locator("#keyword")
            await input_box.fill("") # clear
            await input_box.type("Whitefield", delay=100)
            await asyncio.sleep(2)
            
            # Press Enter to select from autocomplete
            await page.keyboard.press("Enter")
            print(f"[*] Pressed Enter for: {loc}")
            await asyncio.sleep(2)
            
            # Click search button
            search_btn = page.locator(".mb-search__btn")
            if await search_btn.count() > 0:
                await search_btn.first.click()
            else:
                # Try fallback
                await page.keyboard.press("Enter")
            
            # 4. Wait for results
            await page.wait_for_selector(".mb-srp__list", timeout=30000)
            print("[*] Search results loaded.")
            
            # Click Owner filter
            print("[*] Attempting to click 'Owners' filter...")
            try:
                # 1. Click "Posted By" dropdown pill using user's XPath
                posted_by = page.locator("xpath=/html/body/div/div/div/div[2]/div[1]/div/div[2]/div[5]/div")
                if await posted_by.count() > 0:
                    await posted_by.first.click()
                    await asyncio.sleep(2)
                    
                    # 2. Click "Owners" label inside the dropdown
                    owners_label = page.locator("label", has_text="Owners")
                    if await owners_label.count() > 0:
                        await owners_label.first.click()
                        await asyncio.sleep(1)
                        
                        # 3. Click Done
                        done_btn = page.locator("div", has_text="Done").last
                        await done_btn.click()
                        print("[*] Clicked 'Owners' and 'Done'!")
                        await asyncio.sleep(5) # wait for reload
                    else:
                        print("[!] Could not find Owners label")
                else:
                    print("[!] Could not find 'Posted By' filter via XPath")
            except Exception as e:
                print(f"[!] Error clicking Owner filter: {e}")
            
            # 5. Scroll slightly to load links
            for _ in range(5):
                await page.evaluate("window.scrollBy(0, 3000)")
                await asyncio.sleep(1.5)
                
            # 6. Check links
            all_links = await page.locator("a[href]").all()
            
            individual_flats = 0
            projects = 0
            
            for link in all_links:
                try:
                    href = await link.get_attribute("href", timeout=500)
                    if not href: continue
                    href_lower = href.lower()
                    if "propertydetails" in href_lower:
                        individual_flats += 1
                    elif "pdpid-" in href_lower:
                        projects += 1
                except:
                    pass
                    
            print(f"[*] Results for {loc}:")
            print(f"    Builder Projects found: {projects}")
            print(f"    Individual Flats found: {individual_flats}")
            
            if individual_flats > 0:
                print("[SUCCESS] Found real flats for this location!")
            else:
                print("[FAILED] Only found projects/spam.")
                
            await page.close()
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_location_loop())
