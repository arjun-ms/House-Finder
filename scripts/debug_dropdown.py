"""Debug script to inspect what MagicBricks renders in the dropdown after typing."""
import asyncio
from playwright.async_api import async_playwright
import config
from browser_agent import navigate_to_magicbricks, select_rent_tab

async def debug():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
        )
        context = await browser.new_context(user_agent=config.USER_AGENT)
        page = await context.new_page()

        # Use the real functions
        await navigate_to_magicbricks(page)
        await select_rent_tab(page)

        # Find input
        inp = page.locator("#keyword").first
        await inp.focus()
        await asyncio.sleep(0.5)

        # Clear existing pills
        for _ in range(5):
            await page.keyboard.press("Backspace")
            await asyncio.sleep(0.2)
        await inp.fill("")
        await asyncio.sleep(0.3)

        # Type the keyword character by character
        keyword = "Whitefiel"
        print(f"\n[1] Typing '{keyword}' ...")
        await inp.type(keyword, delay=150)
        await asyncio.sleep(4)  # Extra wait for AJAX

        # Screenshot
        await page.screenshot(path="debug_dropdown_screenshot.png", full_page=False)
        print("[2] Screenshot saved to debug_dropdown_screenshot.png")

        # Dump all potential suggest containers
        selectors_to_check = [
            "#serachSuggest",
            ".mb-search__auto-suggest",
            ".mb-search__auto-suggest__list",
            ".sugg-list",
            ".auto-suggest",
            ".pac-container",
            "[class*='suggest']",
            "[id*='suggest']",
            "[id*='Suggest']",
        ]

        for sel in selectors_to_check:
            try:
                loc = page.locator(sel)
                count = await loc.count()
                if count > 0:
                    for j in range(count):
                        el = loc.nth(j)
                        visible = await el.is_visible()
                        html = await el.inner_html()
                        tag = await el.evaluate("el => el.tagName")
                        classes = await el.evaluate("el => el.className")
                        eid = await el.evaluate("el => el.id || ''")
                        print(f"\n[MATCH] selector='{sel}' index={j} tag={tag} id='{eid}' class='{classes}' visible={visible}")
                        print(f"  innerHTML length={len(html)}")
                        if html:
                            print(f"  innerHTML (first 2000):\n{html[:2000]}")
                        else:
                            print("  innerHTML: EMPTY")
            except Exception as e:
                pass

        # Also search for any elements containing 'whitefield' text on page
        print("\n\n[3] Searching page for elements containing 'whitefield' text...")
        wf_elements = page.locator("text=/whitefield/i")
        wf_count = await wf_elements.count()
        print(f"Found {wf_count} elements with 'whitefield' text")
        for i in range(min(wf_count, 15)):
            try:
                el = wf_elements.nth(i)
                text = await el.text_content(timeout=500)
                tag = await el.evaluate("el => el.tagName")
                classes = await el.evaluate("el => el.className || ''")
                visible = await el.is_visible()
                if text and len(text.strip()) < 200:
                    print(f"  [{tag}.{classes}] visible={visible} text='{text.strip()}'")
            except:
                continue

        await browser.close()

asyncio.run(debug())
