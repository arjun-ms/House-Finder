import asyncio
from playwright.async_api import async_playwright
import config

async def dump():
    url = 'https://www.magicbricks.com/gk-tropical-springs-whitefield-bangalore-pdpid-4d4235303333343137'
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(user_agent=config.USER_AGENT)
        page = await context.new_page()
        await page.goto(url, wait_until='domcontentloaded')
        await asyncio.sleep(4)
        
        # Look for buttons or tabs that might contain rent listings
        els = await page.locator("text=/rent/i").all()
        for el in els:
            try:
                t = await el.text_content()
                if t and len(t) < 50:
                    print('FOUND TEXT:', t.strip())
            except: pass
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(dump())
