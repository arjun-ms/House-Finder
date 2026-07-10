import asyncio
from playwright.async_api import async_playwright

async def inspect():
    async with async_playwright() as p:
        import config
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
        )
        context = await browser.new_context(user_agent=config.USER_AGENT)
        page = await context.new_page()
        await page.goto("https://www.magicbricks.com/")
        await asyncio.sleep(3)
        
        # Try to find the search container
        html = await page.evaluate('''() => {
            const searchBox = document.querySelector('.mb-search') || document.querySelector('.search-container') || document.body;
            return searchBox.innerHTML;
        }''')
        
        with open("search_html.txt", "w", encoding="utf-8") as f:
            f.write(html)
            
        print("HTML dumped to search_html.txt")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(inspect())
