import asyncio
from playwright.async_api import async_playwright
import browser_agent

async def test_age_extraction():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        # Search page to set cookies
        page = await context.new_page()
        await page.goto("https://www.magicbricks.com/property-for-rent/residential-real-estate?bedroom=2&proptype=Multistorey-Apartment,Builder-Floor-Apartment,Penthouse,Studio-Apartment&cityName=Bangalore")
        await asyncio.sleep(3)
        
        url = "https://www.magicbricks.com/assetz-marq-whitefield-bangalore-pdpid-4d4235303730313131"
        data = await browser_agent.scrape_property_detail(context, url, 1, 1)
        print("RAW DATA:", data)
        
        html = await page.content()
        with open("debug/test_dom.html", "w", encoding="utf-8") as f:
            f.write(html)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_age_extraction())
