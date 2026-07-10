import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_extra_http_headers({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'})
        print("Navigating...")
        await page.goto("https://www.magicbricks.com/alembic-urban-forest-kadugodi-bangalore-pdpid-4d4235303831323630", wait_until="load", timeout=60000)
        await asyncio.sleep(5)
        print("Dumping...")
        html = await page.content()
        with open("F:/House Finder/test_dom.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("Done!")
        await browser.close()

asyncio.run(main())
