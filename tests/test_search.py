import asyncio
import sys
from playwright.async_api import async_playwright

import pytest
from agents.browser_agent import navigate_to_magicbricks, select_rent_tab, fill_location, click_search

@pytest.mark.asyncio
async def test_search_form():
    print("Running search form interaction test...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # 1. Navigate
            await navigate_to_magicbricks(page)
            
            # 2. Select Rent tab
            await select_rent_tab(page)
            
            # 3. Fill Location
            await fill_location(page, "Whitefield")
            
            # Dump the search form DOM to debug the search button
            try:
                html = await page.evaluate("document.querySelector('.mb-search').outerHTML")
                with open("search_form_debug.html", "w", encoding="utf-8") as f:
                    f.write(html)
            except Exception:
                pass
                
            # 4. Click Search
            await click_search(page)
            
            # 5. Assertions
            await page.wait_for_load_state("domcontentloaded")
            await asyncio.sleep(2)  # Give it a moment to update URL
            current_url = page.url.lower()
            print(f"Resulting URL: {current_url}")
            
            assert "rent" in current_url, "URL does not contain 'rent' - Rent tab selection failed!"
            assert "whitefield" in current_url, "URL does not contain 'whitefield' - Location fill failed!"
            
            print("TEST PASSED: Successfully navigated to Rent properties in Whitefield.")
        except Exception as e:
            print(f"TEST FAILED: {type(e).__name__}: {str(e)}")
            sys.exit(1)
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_search_form())
