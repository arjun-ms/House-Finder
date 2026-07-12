"""
Smart Browser Agent - Playwright automation augmented with LLM for UI resilience.

Handles:
1. Launching headed browser with browser-use Agent
2. Navigating to MagicBricks, interacting with search form via LLM
3. Collecting listing URLs from search results (deterministic parsing)
4. Scraping property details from individual listing pages (deterministic parsing)
"""

import asyncio
import json
import os
import re
from datetime import datetime

from pydantic import BaseModel, Field
import config
from playwright.async_api import Page, async_playwright

from agents.browser_agent import (
    get_dynamic_locations,
    deduplicate_properties,
    collect_properties_from_srp,
    scrape_property_detail
)


def _tool_param(params, name: str):
    """Read browser-use tool params whether they arrive as a model or dict."""
    if isinstance(params, dict):
        return params[name]
    return getattr(params, name)


async def run_browser_agent() -> list[dict]:
    """
    LLM-augmented browser automation pipeline looping over specific localities.
    """
    properties = []
    failed_count = 0
    
    from browser_use import Agent, Browser, Controller, BrowserSession, ChatGoogle
    from agents.agent_tools import AgentTools

    # Configure the Gemini LLM
    from dotenv import load_dotenv
    load_dotenv(override=True)
    if os.environ.get("GEMINI_API_KEY"):
        key = os.environ["GEMINI_API_KEY"]
        print(f"Gemini API key set: {key[:4]}...{key[-4:]}")
        
    llm = ChatGoogle(model=config.LLM_MODEL)

    # Setup the custom tool controller
    controller = Controller()

    @controller.action("Safely click an element by text. Use this for critical navigation steps. If multiple elements have the same text, this will throw an Ambiguity Error.")
    async def safe_click_by_text(text: str, browser_session: BrowserSession):
        page = await browser_session.get_current_page()
        locator = page.locator(f"text=/{text}/i")
        count = await locator.count()
        
        # We need to filter for visible elements
        visible_elements = []
        for i in range(count):
            el = locator.nth(i)
            if await el.is_visible():
                visible_elements.append(el)
                
        visible_count = len(visible_elements)
        if visible_count == 0:
            return f"Error: Found 0 visible elements matching text '{text}'."
        elif visible_count > 1:
            return f"Ambiguity Error: {visible_count} elements found matching '{text}'. Please use 'inspect_clickable_elements' to investigate."
        else:
            await visible_elements[0].click()
            return f"Success: Clicked the only visible element matching '{text}'."

    @controller.action("Inspect the DOM to find all clickable elements containing a specific text. Use this when safe_click_by_text throws an Ambiguity Error.")
    async def inspect_clickable_elements(text: str, browser_session: BrowserSession):
        page = await browser_session.get_current_page()
        tools = AgentTools(page)
        results = await tools.find_clickable_by_text(text, max_results=5)
        simplified = []
        for r in results:
            simplified.append(f"Tag: {r['tag']}, Class: {r['class']}, ID: {r['id']}, Text: {r['text']}, OnClick: {r['onclick']}")
        return f"Found {len(simplified)} elements:\n" + "\n".join(simplified)

    @controller.action("Click an element precisely using a CSS selector. Use this after inspecting the DOM to execute the disambiguated click.")
    async def click_element_by_css(selector: str, browser_session: BrowserSession):
        page = await browser_session.get_current_page()
        try:
            element = page.locator(selector).first
            await element.wait_for(state="attached", timeout=5000)
            await element.evaluate("el => el.click()")
            return f"Success: Clicked element matching CSS selector '{selector}'."
        except Exception as e:
            return f"Failed to click element with selector '{selector}': {e}"

    class CheckboxStateParams(BaseModel):
        dummy: str = Field(default="check", description="A dummy string to satisfy pydantic")

    @controller.action("Inspect the state of BHK checkboxes (e.g. 1 BHK, 2 BHK) to see which ones are currently selected. Returns a list of selected and unselected BHK options.")
    async def inspect_checkbox_state(params: CheckboxStateParams, browser_session: BrowserSession):
        page = await browser_session.get_current_page()
        js_code = """
        () => {
            const inputs = Array.from(document.querySelectorAll('input[name="bhkFlatHouse"]'));
            if (inputs.length === 0) return "Error: Could not find any BHK checkboxes. Ensure the property dropdown is open.";
            
            let result = [];
            inputs.forEach(input => {
                const label = document.querySelector(`label[for="${input.id}"]`);
                const text = label ? label.textContent : input.id;
                const isSelected = input.checked;
                if (text) {
                    result.push("'" + text + "': " + (isSelected ? "SELECTED" : "UNSELECTED"));
                }
            });
            return "Current Filter State:\\n" + result.join("\\n");
        }
        """
        result = await page.evaluate(js_code)
        await asyncio.sleep(6) # Anti-throttle delay
        return result

    class BudgetStateParams(BaseModel):
        dummy: str = Field(default="check", description="A dummy string to satisfy pydantic")

    @controller.action("Inspect the current values of the Min and Max budget inputs.")
    async def inspect_budget_state(params: BudgetStateParams, browser_session: BrowserSession):
        page = await browser_session.get_current_page()
        js_code = """
        () => {
            const minInput = document.querySelector('#budgetMin, #minBudget, input[placeholder*="Min Price"], input[placeholder*="Min"], .min-budget input');
            const maxInput = document.querySelector('#budgetMax, #maxBudget, input[placeholder*="Max Price"], input[placeholder*="Max"], .max-budget input');
            
            if (!minInput && !maxInput) return "Error: Could not find budget inputs. Ensure the budget dropdown is open.";
            
            return "Current Budget State:\\n" + 
                   "Min: " + (minInput ? minInput.value : "Not Found") + "\\n" +
                   "Max: " + (maxInput ? maxInput.value : "Not Found");
        }
        """
        result = await page.evaluate(js_code)
        await asyncio.sleep(6) # Anti-throttle delay
        return result

    class SetBhkParams(BaseModel):
        target_bhk: str = Field(description="The BHK to select, e.g., '2 BHK'")

    @controller.action("Deterministically set the BHK filter to strictly match the requested string (unchecks all others).")
    async def set_bhk_filter(params: SetBhkParams, browser_session: BrowserSession):
        page = await browser_session.get_current_page()
        target_bhk = params.target_bhk if hasattr(params, 'target_bhk') else params.get('target_bhk', '2 BHK')
        js_code = f"""
        () => {{
            const inputs = Array.from(document.querySelectorAll('input[name="bhkFlatHouse"]'));
            if (inputs.length === 0) return "Error: Could not find BHK checkboxes. Please ensure the property dropdown is open first.";
            
            let changed = 0;
            inputs.forEach(input => {{
                const label = document.querySelector(`label[for="${{input.id}}"]`);
                const text = label ? label.textContent.trim() : "";
                
                const shouldBeChecked = text.toLowerCase().includes("{target_bhk.lower()}");
                
                if (shouldBeChecked && !input.checked) {{
                    label ? label.click() : input.click();
                    changed++;
                }} else if (!shouldBeChecked && input.checked) {{
                    label ? label.click() : input.click();
                    changed++;
                }}
            }});
            return "Success: BHK filter adjusted strictly to '{target_bhk}'.";
        }}
        """
        result = await page.evaluate(js_code)
        await asyncio.sleep(6) # Anti-throttle delay
        return result

    class SetBudgetParams(BaseModel):
        min_budget: str = Field(description="Minimum budget limit")
        max_budget: str = Field(description="Maximum budget limit")

    @controller.action("Deterministically set the Min and Max budget inputs.")
    async def set_budget_filter(params: SetBudgetParams, browser_session: BrowserSession):
        page = await browser_session.get_current_page()
        min_budget = params.min_budget if hasattr(params, 'min_budget') else params.get('min_budget', '30000')
        max_budget = params.max_budget if hasattr(params, 'max_budget') else params.get('max_budget', '40000')
        js_code = f"""
        () => {{
            const minInput = document.querySelector('#budgetMin, #minBudget, input[placeholder*="Min Price"], input[placeholder*="Min"], .min-budget input');
            const maxInput = document.querySelector('#budgetMax, #maxBudget, input[placeholder*="Max Price"], input[placeholder*="Max"], .max-budget input');
            
            if (!minInput || !maxInput) return "Error: Could not find budget inputs. Please ensure the budget dropdown is open first.";
            
            minInput.value = "{min_budget}";
            minInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
            minInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
            
            maxInput.value = "{max_budget}";
            maxInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
            maxInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
            
            return "Success: Budget strictly set to {min_budget} - {max_budget}.";
        }}
        """
        result = await page.evaluate(js_code)
        await asyncio.sleep(6) # Anti-throttle delay
        return result

    print(f"[*] Extracting dynamic localities for '{config.SEARCH_KEYWORD}' to avoid sponsored listing floods...")
    async with async_playwright() as p:
        temp_browser = await p.chromium.launch(headless=not config.HEADED)
        temp_ctx = await temp_browser.new_context()
        temp_page = await temp_ctx.new_page()
        locations_to_test = await get_dynamic_locations(temp_page, config.SEARCH_KEYWORD)
        await temp_browser.close()

    for loc in locations_to_test:
        print(f"\n{'='*50}\n[*] Starting search for location: {loc}\n{'='*50}")
        
        browser = Browser(
            headless=not config.HEADED,
            record_video_dir=config.VIDEO_DIR if config.RECORD_VIDEO else None,
            keep_alive=True,
            args=[
                '--disable-notifications',
                '--disable-popup-blocking',
                '--disable-infobars',
                '--disable-dev-shm-usage'
            ]
        )
        
        prompt = f"""
        Go to {config.MAGICBRICKS_URL}.
        RULE: For critical navigation steps like clicking "Rent", use `safe_click_by_text`. If it throws an Ambiguity Error, you MUST NOT guess. You must use `inspect_clickable_elements` to read the HTML, and then use `click_element_by_css` to click the correct element.
        RULE: Do NOT scroll down until you have completed ALL filter steps. Stay at the top of the page while setting filters.
        
        Step 1: Use this strategy to switch to Rental mode reliably.
        Step 2: In the main location search box, type exactly '{loc}'. 
        Wait for the auto-suggest dropdown and click the item that exactly matches '{loc}'.
        Step 3: Open the BHK/Property Type filter dropdown. 
        Step 4: IMPORTANT: Call `set_bhk_filter` with target_bhk '{config.BHK_TYPE}' to automatically select {config.BHK_TYPE} and uncheck everything else. Verify it using `inspect_checkbox_state` just in case.
        Step 5: Open the Budget filter dropdown. 
        Step 6: Call `set_budget_filter` with min_budget '{config.MIN_BUDGET}' and max_budget '{config.MAX_BUDGET}'. Verify using `inspect_budget_state`.
        Step 7: Click the main Search button to execute the search.
        Step 8: Once the search results page loads (you should see property cards), look for 'Posted By' or 'Owner' filter (often a checkbox or tab on the left/top) and select 'Owner'. DO NOT click on links like "Owner Properties" that open a new tab and abandon the current search state. Only use on-page filters.
        Wait for the filtered results to load.
        Once the search results are fully visible and filtered, check the page one last time to ensure filters are active, then stop and finish the task.
        """
        
        agent = Agent(
            task=prompt,
            llm=llm,
            browser=browser,
            controller=controller,
            use_vision=False
        )
        
        try:
            print("[*] Starting LLM Agent for UI navigation...")
            await agent.run()
            print("[*] LLM Agent finished navigation.")
            
            print("[*] Handing over to deterministic parser...")
            async with async_playwright() as p:
                print(f"[*] Connecting Playwright to CDP at {browser.cdp_url}")
                pw_browser = await p.chromium.connect_over_cdp(browser.cdp_url)
                pw_context = pw_browser.contexts[0]
                pw_page = pw_context.pages[-1]
                
                # Collect Properties directly from Search Results Page
                props = await collect_properties_from_srp(pw_page)
                
                if not props:
                    print(f"[!] No properties collected for {loc}")
                    failed_count += 1
                    await pw_browser.close()
                    continue
                    
                print(f"[*] Navigating to {len(props)} Property Detail Pages for Stage 2 data...")
                detailed_props = []
                for prop in props:
                    dp = await scrape_property_detail(pw_context, prop)
                    if dp:
                        detailed_props.append(dp)
                
                properties.extend(detailed_props)
                await pw_browser.close()
                
        except Exception as e:
            print(f"[!] Critical error in LLM agent loop: {e}")
            failed_count += 1
        finally:
            await browser.stop()
            
    print(f"\n{'='*60}\nALL LOCATIONS SCRAPED\n  Succeeded: {len(properties)}\n  Failed: {failed_count}\n{'='*60}\n")
    
    # Deduplicate properties
    before_dedup = len(properties)
    properties = deduplicate_properties(properties)
    if before_dedup != len(properties):
        print(f"[*] Deduplication: {before_dedup} -> {len(properties)} unique properties")
        
    return properties


# Keep the same deep scraper since it's deterministic and reliable
# async def scrape_details_for_urls(props: list[dict]) -> list[dict]:
#     results = []
#     async with async_playwright() as p:
#         playwright_browser = await p.chromium.launch(headless=not config.HEADED)
#         context = await playwright_browser.new_context(viewport={'width': 1280, 'height': 800})
        
#         for i, prop in enumerate(props):
#             url = prop.get("listing_url")
#             print(f"  [{i+1}/{len(props)}] Deep scraping: {str(prop.get('property_name', url))[:40]}...")
#             data = await scrape_property_detail(context, prop)
#             if data:
#                 results.append(data)
                
#         await playwright_browser.close()
#     return results

if __name__ == "__main__":
    asyncio.run(run_browser_agent())
