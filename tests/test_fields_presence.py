import asyncio
import config
from agents.browser_agent import run_browser_agent

async def check():
    config.LOCATION_KEYWORD = "Koramangala, Bangalore"
    config.MAX_LISTINGS_TO_SCRAPE = 20
    
    # run_browser_agent will return a list of completely scraped dictionaries
    # (It inherently uses parse_srp_card_html and scrape_property_detail)
    results = await run_browser_agent()
    
    # Filter to standard props
    results = [r for r in results if r.get('listing_url') and 'pdpid' not in r.get('listing_url')]
    
    print("\n=== PRESENCE RESULTS ===")
    floor_count = sum(1 for r in results if r.get('floor_number') is not None)
    age_count = sum(1 for r in results if r.get('property_age') is not None)
    balcony_count = sum(1 for r in results if r.get('balcony_count') is not None)
    
    print(f"Total standard properties checked: {len(results)}")
    print(f"Floor present:   {floor_count}/{len(results)}")
    print(f"Age present:     {age_count}/{len(results)}")
    print(f"Balcony present: {balcony_count}/{len(results)}")
    
    print("\nSample of missing fields:")
    for r in results:
        missing = []
        if r.get('floor_number') is None: missing.append("Floor")
        if r.get('property_age') is None: missing.append("Age")
        if r.get('balcony_count') is None: missing.append("Balcony")
        
        if missing:
            print(f"- {r['listing_url'].split('/')[-1][:30]}... is missing: {', '.join(missing)}")

if __name__ == "__main__":
    asyncio.run(check())
