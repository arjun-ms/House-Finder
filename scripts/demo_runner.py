import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

import asyncio
from agents.browser_agent import (
    launch_browser, navigate_to_magicbricks, select_rent_tab, 
    fill_location, apply_bhk_filter, apply_budget_filter, 
    apply_more_filters, click_search, collect_properties_from_srp,
    scrape_property_detail, get_dynamic_locations
)
import config


# RUN ONLY UNTIL BROWSER SCRAPING ; No Data Passing into LLM
async def main():
    print("="*60)
    print("Starting Deterministic Demo Runner (Bypasses AI Quotas)")
    print("="*60)
    
    playwright, browser, context, temp_page = await launch_browser()
    
    locations_to_test = await get_dynamic_locations(temp_page, config.SEARCH_KEYWORD)
    await temp_page.close()
    
    all_detailed_props = []
    
    for loc in locations_to_test:
        print(f"\n{'='*50}\n[*] Starting search for location: {loc}\n{'='*50}")
        # Need a fresh page for each location search
        page = await context.new_page()
        
        try:
            await navigate_to_magicbricks(page)
            await select_rent_tab(page)
            await fill_location(page, loc)
            await apply_bhk_filter(page)
            await apply_budget_filter(page)
            await apply_more_filters(page, floor_option=config.MIN_FLOOR)
            await click_search(page)
            
            props = await collect_properties_from_srp(page)
            print(f"\n[*] Extracted {len(props)} properties from SRP for {loc}. Navigating to Property Detail Pages for Stage 2 data...")
            
            detailed_props = []
            for p in props:
                dp = await scrape_property_detail(context, p)
                if dp:
                    detailed_props.append(dp)
            
            all_detailed_props.extend(detailed_props)
                    
            print(f"[*] Successfully scraped {len(detailed_props)} detailed properties for {loc}.")
            
        except Exception as e:
            print(f"\n[!] Error during demo run for {loc}: {e}")
        finally:
            await page.close()
            
    print(f"\n[*] Demo Complete! Successfully scraped {len(all_detailed_props)} detailed properties in total.")
    print(f"[*] Video saved to {config.VIDEO_DIR}")
    
    await browser.close()
    await playwright.stop()

if __name__ == "__main__":
    asyncio.run(main())
