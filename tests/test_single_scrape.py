import asyncio
from playwright.async_api import async_playwright
from agents.browser_agent import scrape_property_detail
import config
import json

async def test_single_scrape():
    prop = {
        "listing_url": "https://www.magicbricks.com/gk-tropical-springs-whitefield-bangalore-pdpid-4d4235303333343137",
        "property_name": "Test Property"
    }
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(user_agent=config.USER_AGENT)
        result = await scrape_property_detail(context, prop)
        print("SCRAPE RESULT:")
        print(json.dumps(result, indent=2))
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_single_scrape())
