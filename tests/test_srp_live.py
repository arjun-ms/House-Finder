import asyncio
from playwright.async_api import async_playwright
import browser_agent
import config

async def test_srp_extraction_live():
    config.MAX_LISTINGS_TO_SCRAPE = 3
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        context = await browser.new_context(
            viewport={"width": 1366, "height": 768},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        tools = browser_agent.AgentTools(page)
        
        await browser_agent.navigate_to_magicbricks(page, tools)
        await asyncio.sleep(2)
        await browser_agent.select_rent_tab(page, tools)
        await asyncio.sleep(2)
        
        await browser_agent.fill_location(page, "Whitefield", tools)
        await asyncio.sleep(2)
        await browser_agent.apply_bhk_filter(page, tools)
        await browser_agent.apply_budget_filter(page, tools)
        await browser_agent.click_search(page, tools)
        
        await page.wait_for_selector(".mb-srp__list", state="attached", timeout=30000)
        await asyncio.sleep(5)
        
        # Test our new function
        properties = await browser_agent.collect_properties_from_srp(page)
        
        print("\n=== EXTRACTION RESULTS ===")
        for i, p in enumerate(properties):
            print(f"[{i+1}] {p.get('property_name')}")
            print(f"  Price: {p.get('price')}")
            print(f"  Floor: {p.get('floor_number')} / {p.get('total_floors')}")
            print(f"  Balcony: {p.get('balcony_count')}")
            print(f"  Area: {p.get('built_up_area')}")
            print(f"  URL: {p.get('listing_url')}")
            print("-" * 40)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_srp_extraction_live())
