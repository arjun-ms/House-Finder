"""
Smart Browser Agent - Playwright automation augmented with LLM for UI resilience.

Handles:
1. Launching headed browser with browser-use Agent
2. Navigating to MagicBricks, interacting with search form via LLM
3. Collecting listing URLs from search results (deterministic parsing)
4. Scraping property details from individual listing pages (deterministic parsing)
"""

import asyncio
import os
import re
from datetime import datetime

import config
from browser_use import Agent, Browser, ChatGoogle
from playwright.async_api import Page, async_playwright

from browser_agent import (
    get_dynamic_locations,
    deduplicate_properties,
    collect_properties_from_srp,
    scrape_property_detail
)

async def run_browser_agent() -> list[dict]:
    """
    LLM-augmented browser automation pipeline looping over specific localities.
    """
    properties = []
    failed_count = 0
    
    # Configure the Gemini LLM
    from dotenv import load_dotenv
    load_dotenv()
    if not os.environ.get("GOOGLE_API_KEY") and os.environ.get("GEMINI_API_KEY"):
        os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]
        
    llm = ChatGoogle(model="gemini-2.5-flash") # Gemini 2.5 Flash is great for agentic web tasks
    
    # Configure the browser-use browser
    browser = Browser(headless=not config.HEADED)
    
    locations_to_test = [config.SEARCH_KEYWORD]
    
    for loc in locations_to_test:
        print(f"\n{'='*60}\nSmart Scraping Location: {loc}\n{'='*60}")
        
        # Comprehensive prompt combining navigation, search, and filtering
        prompt = f"""
        Go to {config.MAGICBRICKS_URL}.
        Click on the 'Rent' tab to switch to rental search mode.
        In the main location search box, type exactly '{loc}'. 
        Wait for the auto-suggest dropdown and click the item that matches '{loc}'.
        Open the BHK property type filter. Make sure ONLY '{config.BHK_TYPE}' is selected (uncheck others).
        Open the Budget filter. Set the minimum budget to {config.MIN_BUDGET} and maximum to {config.MAX_BUDGET}.
        Click the 'More Filters' or 'Filters' button. Find the 'Floor' section and select '{config.MIN_FLOOR}+' or equivalent.
        Click the main Search button to execute the search.
        Once the search results page loads (you should see property cards), click on the 'Owners' filter (posted by Owners) and click Done.
        Wait for the filtered results to load.
        Once the search results are fully visible and filtered, stop and finish the task.
        """
        
        # We use the browser directly
        agent = Agent(
            task=prompt,
            llm=llm,
            browser=browser
        )
        
        try:
            print("[*] Starting LLM Agent for UI navigation...")
            await agent.run()
            print("[*] LLM Agent finished navigation.")
            
            # Now the browser should be on the SRP (Search Results Page)
            # Get the Playwright page from the browser directly
            page = await browser.get_current_page()
            
            print("[*] Handing over to deterministic parser...")
            # Collect Properties directly from Search Results Page
            props = await collect_properties_from_srp(page)
            
            if not props:
                print(f"[!] No properties collected for {loc}")
                failed_count += 1
            else:
                print(f"[*] Collected {len(props)} properties for {loc}!")
                properties.extend(props)
                
        except Exception as e:
            print(f"[!] Critical error in LLM agent loop: {e}")
            failed_count += 1
            
    print(f"\n{'='*60}\nALL LOCATIONS SCRAPED\n  Succeeded: {len(properties)}\n  Failed: {failed_count}\n{'='*60}\n")
    
    # Deduplicate properties
    before_dedup = len(properties)
    properties = deduplicate_properties(properties)
    if before_dedup != len(properties):
        print(f"[*] Deduplication: {before_dedup} -> {len(properties)} unique properties")
        
    await browser.close()
    return properties


# Keep the same deep scraper since it's deterministic and reliable
async def scrape_details_for_urls(props: list[dict]) -> list[dict]:
    results = []
    async with async_playwright() as p:
        playwright_browser = await p.chromium.launch(headless=not config.HEADED)
        context = await playwright_browser.new_context(viewport={'width': 1280, 'height': 800})
        
        for i, prop in enumerate(props):
            url = prop.get("listing_url")
            print(f"  [{i+1}/{len(props)}] Deep scraping: {str(prop.get('property_name', url))[:40]}...")
            data = await scrape_property_detail(context, prop)
            if data:
                results.append(data)
                
        await playwright_browser.close()
    return results

if __name__ == "__main__":
    asyncio.run(run_browser_agent())
