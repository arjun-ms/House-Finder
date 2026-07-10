import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        print("Navigating to MagicBricks...")
        await page.goto("https://www.magicbricks.com/property-for-rent/residential-real-estate?bedroom=2&proptype=Multistorey-Apartment,Builder-Floor-Apartment,Penthouse,Studio-Apartment,Residential-House,Villa&cityName=Bangalore")
        
        print("Waiting for results to load...")
        try:
            await page.wait_for_selector(".mb-srp__card", timeout=45000)
        except Exception as e:
            print("Timeout waiting for card, dumping whatever we have")
            
        await asyncio.sleep(5)  # Let dynamic JS finish loading filters
        
        # Dump the top filter bar and left sidebar filters
        print("Dumping filter DOM...")
        html = await page.evaluate('''() => {
            let filterElements = document.querySelectorAll('.filter-container, .mb-srp__tabs, .mb-srp__header, .mb-filter, [class*="filter"]');
            let result = "";
            filterElements.forEach(e => result += e.outerHTML + "\\n\\n");
            return result || document.body.innerHTML;
        }''')
        
        with open("dom_dump.html", "w", encoding="utf-8") as f:
            f.write(html)
            
        print("DOM dumped to dom_dump.html")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
