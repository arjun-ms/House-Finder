import asyncio
from playwright.async_api import async_playwright

async def extract_dom():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        print("Navigating to MagicBricks homepage...")
        await page.goto("https://www.magicbricks.com/", wait_until="domcontentloaded")
        await asyncio.sleep(5) # Let dynamic content load
        
        print("Extracting homepage DOM...")
        homepage_html = await page.content()
        with open("magicbricks_homepage.html", "w", encoding="utf-8") as f:
            f.write(homepage_html)
        print("Saved homepage DOM to magicbricks_homepage.html")
        
        # Now let's try to get a property listing page directly to see its structure
        listing_url = "https://www.magicbricks.com/property-details/2-bhk-flat-for-rent-in-whitefield-bangalore-pdpid-4d4234373335383531"
        print(f"Navigating to listing page: {listing_url}")
        try:
            await page.goto(listing_url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(5)
            
            print("Extracting listing page DOM...")
            listing_html = await page.content()
            with open("magicbricks_listing.html", "w", encoding="utf-8") as f:
                f.write(listing_html)
            print("Saved listing page DOM to magicbricks_listing.html")
        except Exception as e:
            print(f"Failed to extract listing page: {e}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(extract_dom())
