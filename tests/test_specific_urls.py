import asyncio
from playwright.async_api import async_playwright
import config
from agents.browser_agent import scrape_property_detail
import json

async def check():
    urls = [
        "https://www.magicbricks.com/propertyDetails/2-BHK-1200-Sq-ft-Multistorey-Apartment-FOR-Rent-Nallurhalli-in-Bangalore&id=4d423835333135303933",
        "https://www.magicbricks.com/propertyDetails/2-BHK-1116-Sq-ft-Multistorey-Apartment-FOR-Rent-Vijayanagara-in-Bangalore&id=4d423834333032393431",
        "https://www.magicbricks.com/propertyDetails/2-BHK-1400-Sq-ft-Multistorey-Apartment-FOR-Rent-Thubarahalli-in-Bangalore&id=4d423835333230323633"
    ]
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(user_agent=config.USER_AGENT)
        
        for u in urls:
            dummy_prop = {
                "listing_url": u,
                "property_name": None,
                "price": None,
                "location": None,
                "bhk_config": None,
                "floor_number": None,
                "total_floors": None,
                "property_age": None,
                "balcony_count": None,
                "built_up_area": None,
                "furnishing_status": None,
                "amenities": [],
                "builder_society": None,
            }
            res = await scrape_property_detail(context, dummy_prop)
            if not res:
                print(f"FAILED TO SCRAPE: {u}")
                continue
            print("\n-------------------------")
            print(f"URL: {u}")
            print(f"Price: {res.get('price')}")
            print(f"Floor: {res.get('floor_number')} / {res.get('total_floors')}")
            print(f"Age: {res.get('property_age')}")
            print(f"Area: {res.get('built_up_area')}")
            print(f"Furnishing: {res.get('furnishing_status')}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(check())
