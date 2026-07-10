import asyncio
from playwright.async_api import async_playwright

async def dump_dom():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Test on a project page
        url = "https://www.magicbricks.com/assetz-marq-whitefield-bangalore-pdpid-4d4235303730313131"
        await page.goto(url, wait_until="domcontentloaded")
        await asyncio.sleep(3)
        html = await page.content()
        with open("debug/dom.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("DOM dumped")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(dump_dom())
