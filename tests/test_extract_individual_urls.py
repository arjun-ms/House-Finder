import asyncio
from playwright.async_api import async_playwright
import config

async def test_extract_individual_urls_from_project_page():
    # A known project page that we struggled to get exact details from
    url = "https://www.magicbricks.com/gk-tropical-springs-whitefield-bangalore-pdpid-4d4235303333343137"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(user_agent=config.USER_AGENT)
        
        try:
            from agents.browser_agent import extract_individual_urls_from_project_page
            urls = await extract_individual_urls_from_project_page(context, url)
            
            # Assertions
            assert isinstance(urls, list), "Expected a list of URLs"
            assert len(urls) > 0, "Expected at least one individual property URL"
            assert "-pdpid-" not in urls[0], f"Found another project page instead of individual listing: {urls[0]}"
            
            print("TEST PASSED: Successfully extracted individual URLs from project page.")
            for u in urls:
                print(f" -> {u}")
        except Exception as e:
            print(f"TEST FAILED: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_extract_individual_urls_from_project_page())
