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
        
        try:
            loc = page.locator('text="Properties for Rent"').first
            await loc.scroll_into_view_if_needed()
            await asyncio.sleep(1)
            await loc.click(timeout=3000)
            await asyncio.sleep(3)
        except Exception as e:
            print('Could not click Properties for Rent:', e)
            
        links = await page.locator('a').all()
        found = []
        for a in links:
            try:
                href = await a.get_attribute('href')
                if href and ('gk-tropical' in href.lower() or 'rent' in href.lower()) and href != url:
                    found.append(href)
            except: pass
        print(f'FOUND {len(found)} propertyDetails links after click')
        for f in set(found[:10]):
            print(f)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(dump())
