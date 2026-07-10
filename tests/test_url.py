import asyncio
from playwright.async_api import async_playwright

async def test_real_url():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False) # See what happens
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        url = "https://www.magicbricks.com/brigade-cosmopolis-whitefield-bangalore-pdpid-4d4235303237383137"
        
        print("Navigating...")
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            print("Loaded DOM")
            await asyncio.sleep(5)
            print("Title:", await page.title())
        except Exception as e:
            print("Error:", e)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_real_url())
