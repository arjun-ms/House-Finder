import asyncio
from playwright.async_api import async_playwright
import config

async def test_owner_filter():
    print("[*] Launching browser...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={'width': 1280, 'height': 800})
        page = await context.new_page()
        
        try:
            print("[*] Navigating to Whitefield...")
            # We'll use a direct search URL for Whitefield to skip the homepage search bar for speed
            url = "https://www.magicbricks.com/property-for-rent/residential-real-estate?bedroom=2&proptype=Multistorey-Apartment,Builder-Floor-Apartment,Penthouse,Studio-Apartment,Service-Apartment&Locality=Whitefield&cityName=Bangalore"
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(5)
            
            print("[*] Attempting to click 'Owners' filter...")
            
            # Replicating the logic from agents.browser_agent.py
            posted_by = page.locator("xpath=/html/body/div/div/div/div[2]/div[1]/div/div[2]/div[5]/div")
            if await posted_by.count() > 0:
                await posted_by.first.click()
                print("  - Clicked 'Posted By' dropdown")
                await asyncio.sleep(2)
                
                owners_label = page.locator("label", has_text="Owners")
                if await owners_label.count() > 0:
                    await owners_label.first.click()
                    print("  - Clicked 'Owners' label")
                    await asyncio.sleep(1)
                    
                    # The specific CSS selector from the user
                    done_btn = page.locator("#body > div.top-filter > div > div.top-filter__item-all-filter > div:nth-child(5) > div > div.filter__component__drop-down > div.filter__component__cta-done")
                    if await done_btn.count() > 0:
                        await done_btn.first.click()
                        print("  - Clicked 'Done' using exact CSS selector!")
                    else:
                        print("  [!] Exact CSS selector not found. Falling back to generic 'Done'...")
                        await page.locator("div", has_text="Done").last.click()
                    
                    print("[*] Success! Filter applied.")
                    await asyncio.sleep(5)  # Wait to observe the result
                else:
                    print("  [!] Could not find Owners label")
            else:
                print("  [!] Could not find 'Posted By' filter via XPath")
                
        except Exception as e:
            print(f"[!] Error: {e}")
        finally:
            await browser.close()
            print("[*] Browser closed.")

if __name__ == "__main__":
    asyncio.run(test_owner_filter())
