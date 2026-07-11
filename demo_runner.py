import asyncio
from browser_agent import (
    launch_browser, navigate_to_magicbricks, select_rent_tab, 
    fill_location, apply_bhk_filter, apply_budget_filter, 
    apply_more_filters, click_search, collect_properties_from_srp
)
import config

async def main():
    print("="*60)
    print("Starting Deterministic Demo Runner (Bypasses AI Quotas)")
    print("="*60)
    
    playwright, browser, context, page = await launch_browser()
    
    loc = "Whitefield"
    
    try:
        await navigate_to_magicbricks(page)
        await select_rent_tab(page)
        await fill_location(page, loc)
        await apply_bhk_filter(page)
        await apply_budget_filter(page)
        await apply_more_filters(page, floor_option=config.MIN_FLOOR)
        await click_search(page)
        
        props = await collect_properties_from_srp(page)
        print(f"\n[*] Demo Complete! Successfully scraped {len(props)} properties.")
        print(f"[*] Video saved to {config.VIDEO_DIR}")
        
    except Exception as e:
        print(f"\n[!] Error during demo run: {e}")
    finally:
        await browser.close()
        await playwright.stop()

if __name__ == "__main__":
    asyncio.run(main())
