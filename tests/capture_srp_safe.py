import asyncio
from playwright.async_api import async_playwright
import browser_agent

async def test_srp_extraction():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        context = await browser.new_context(
            viewport={"width": 1366, "height": 768},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        tools = browser_agent.AgentTools(page)
        
        # Run exactly as the main agent does to bypass anti-bot
        await browser_agent.navigate_to_magicbricks(page, tools)
        await asyncio.sleep(2)
        await browser_agent.select_rent_tab(page, tools)
        await asyncio.sleep(2)
        
        # Search for Whitefield
        await browser_agent.fill_location(page, "Whitefield", tools)
        await asyncio.sleep(2)
        await browser_agent.apply_bhk_filter(page, tools)
        await browser_agent.apply_budget_filter(page, tools)
        await browser_agent.click_search(page, tools)
        
        # Wait for SRP
        await page.wait_for_selector(".mb-srp__list", state="attached", timeout=30000)
        await asyncio.sleep(5)
        
        # Dump the HTML of the first 5 cards
        cards = await page.locator(".mb-srp__card").all()
        html_content = ""
        for i, card in enumerate(cards[:5]):
            html_content += f"\n\n<!-- CARD {i} -->\n"
            html_content += await card.inner_html()
            
        with open("tests/fixtures/srp_cards.html", "w", encoding="utf-8") as f:
            f.write(html_content)
            
        print(f"Dumped {len(cards)} cards to srp_cards.html")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_srp_extraction())
