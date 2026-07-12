"""
TDD: Search Form Verification Tests

Verifies each step of the MagicBricks search form in isolation
against the LIVE site. Catches DOM changes and selector breakage.

Run with:
  python -m pytest tests/test_search_form.py -v -s --tb=short
"""

import pytest
import asyncio
import json
from playwright.async_api import async_playwright, Page

import config

# pytest-asyncio auto mode so we don't need @pytest.mark.asyncio everywhere
pytestmark = pytest.mark.asyncio(loop_scope="module")


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture(autouse=True)
def set_test_config():
    """Lock config to known values for every test."""
    config.SEARCH_KEYWORD = "Whitefield"
    config.CITY = "Bangalore"
    config.BHK_TYPE = "2 BHK"
    config.MIN_BUDGET = 30000
    config.MAX_BUDGET = 40000
    config.HEADED = False
    yield


# Module-scoped shared page: launched once, tests run in order on same page.
_page_holder = {}


async def _get_page():
    """Lazy-init a shared browser page for the whole module."""
    if "page" not in _page_holder:
        pw = await async_playwright().start()
        browser = await pw.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-notifications",
            ],
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent=config.USER_AGENT,
        )
        page = await context.new_page()

        async def block_ads(route):
            url = route.request.url
            if "home-interior" in url.lower() or "hp_toolsandadvicesection" in url.lower():
                await route.abort()
            else:
                await route.continue_()

        await context.route("**/*", block_ads)
        page.on("dialog", lambda dialog: asyncio.create_task(dialog.accept()))
        _page_holder["page"] = page
        _page_holder["browser"] = browser
        _page_holder["pw"] = pw
    return _page_holder["page"]


# =============================================================================
# TEST 1: Navigate
# =============================================================================

async def test_01_navigate_to_magicbricks():
    page = await _get_page()
    await page.goto("https://www.magicbricks.com/", wait_until="domcontentloaded")
    await asyncio.sleep(3)

    assert await page.locator(".mb-search").count() > 0, (
        f"Search form not found. URL: {page.url}"
    )
    print("\n[PASS] MagicBricks loaded.")


# =============================================================================
# TEST 2: Rent tab
# =============================================================================

async def test_02_select_rent_tab():
    page = await _get_page()
    rent_tab = page.locator("#tabRENT")
    assert await rent_tab.count() > 0, "#tabRENT not found."
    await rent_tab.evaluate("el => el.click()")
    await asyncio.sleep(1)

    cat = await page.evaluate('document.getElementById("categoryType")?.value')
    assert cat == "R", f"categoryType should be 'R', got '{cat}'"
    print("\n[PASS] Rent tab selected.")


# =============================================================================
# TEST 3: Fill location
# =============================================================================

async def test_03_fill_location():
    page = await _get_page()
    input_box = page.locator("#keyword")
    await input_box.evaluate("el => el.click()")
    await asyncio.sleep(1)
    
    await input_box.fill("")
    for char in "Whitefield":
        await input_box.type(char, delay=150)
    await asyncio.sleep(3)

    suggest = page.locator("#serachSuggest")
    await suggest.wait_for(state="visible", timeout=10000)
    items = page.locator("#serachSuggest .mb-search__auto-suggest__item")
    count = await items.count()
    assert count > 0, "No suggestions for 'Whitefield'."

    clicked = False
    for i in range(count):
        text = (await items.nth(i).text_content() or "").strip()
        onclick = await items.nth(i).get_attribute("onclick") or ""
        if "whitefield" in text.lower() and "locality" in onclick.lower():
            await items.nth(i).click()
            clicked = True
            print(f"\n[PASS] Selected: '{text}'")
            break

    assert clicked, "No Whitefield locality match found."
    await asyncio.sleep(2)


# =============================================================================
# TEST 3b: Clear previous location when adding a new one
# =============================================================================

async def test_03b_clear_previous_location():
    page = await _get_page()
    
    # 1. We already have 'Whitefield' from test 3. Let's verify it's there.
    pills = page.locator(".mb-search__tag")
    count_before = await pills.count()
    assert count_before >= 1, f"Expected at least 1 location pill, found {count_before}"
    
    # 2. Use browser_agent's exact pill clearing logic or try to clear it.
    print(f"[*] Found {count_before} pills. Attempting to clear...")
    
    # Let's try closing them by clicking their 'close' buttons explicitly
    close_btns = page.locator(".mb-search__tag-close, .mb-search__tag .icon-close")
    close_count = await close_btns.count()
    
    if close_count > 0:
        print(f"[*] Found {close_count} close buttons. Clicking them...")
        for i in range(close_count):
            try:
                await close_btns.first.evaluate("el => el.click()")
                await asyncio.sleep(0.5)
            except Exception:
                pass
    else:
        print("[!] No explicit close buttons found. Falling back to Backspace on input...")
        input_box = page.locator("#keyword")
        await input_box.evaluate("el => el.click()")
        for _ in range(5):
            await page.keyboard.press("Backspace")
            await asyncio.sleep(0.2)
            
    # 3. Verify it's actually cleared
    count_after = await pills.count()
    assert count_after == 0, f"Failed to clear previous locations! Still found {count_after} pills. This causes the 'Promoted Builder Projects' ad spam."
    print("\n[PASS] Previous location pills successfully cleared.")
    
    # 4. Now add the new location
    input_box = page.locator("#keyword")
    await input_box.evaluate("el => el.click()")
    await input_box.fill("")
    for char in "Indiranagar":
        await input_box.type(char, delay=150)
    await asyncio.sleep(3)
    
    suggest = page.locator("#serachSuggest")
    await suggest.wait_for(state="visible", timeout=10000)
    items = page.locator("#serachSuggest .mb-search__auto-suggest__item")
    await items.first.click()
    await asyncio.sleep(2)
    
    count_final = await pills.count()
    assert count_final == 1, f"Expected exactly 1 pill for Indiranagar, got {count_final}"
    print("[PASS] Successfully swapped Whitefield for Indiranagar without stacking.")
    
    # Put it back to Whitefield for the rest of the tests to pass (they expect Whitefield in URL)
    await close_btns.first.evaluate("el => el.click()")
    await asyncio.sleep(0.5)
    await input_box.evaluate("el => el.click()")
    await input_box.fill("")
    for char in "Whitefield":
        await input_box.type(char, delay=150)
    await asyncio.sleep(3)
    await items.first.click()
    await asyncio.sleep(2)


async def test_04_open_property_dropdown():
    page = await _get_page()

    prop_dropdown = page.locator("#propType_rent .mb-search__title").first
    assert await prop_dropdown.count() > 0, "#propType_rent .mb-search__title not found."
    await prop_dropdown.evaluate("el => el.click()")
    await asyncio.sleep(1)

    dropdown = page.locator("#propType_rent .mb-search__dropdown")
    assert await dropdown.count() > 0, "Dropdown panel did not appear."

    prop_types = await page.evaluate("""
    () => {
        return ['residential_0', 'residential_1'].map(id => {
            const cb = document.getElementById(id);
            const label = document.querySelector('label[for="' + id + '"]');
            return {
                id: id,
                checked: cb ? cb.checked : null,
                label: label ? label.textContent.trim() : 'N/A'
            };
        });
    }
    """)
    print(f"\n  Property types: {json.dumps(prop_types, indent=2)}")

    flat = next((p for p in prop_types if p["id"] == "residential_0"), None)
    assert flat and flat["checked"] is True, (
        f"'Flat' should be checked by default. State: {prop_types}"
    )
    print("[PASS] Property dropdown opened. 'Flat' is checked.")


# =============================================================================
# TEST 5: Verify BHK checkboxes exist
# =============================================================================

async def test_05_bhk_checkboxes_exist():
    page = await _get_page()

    bhk_state = await page.evaluate("""
    () => {
        const inputs = document.querySelectorAll('input[name="bhkFlatHouse"]');
        return Array.from(inputs).map(input => {
            const label = document.querySelector('label[for="' + input.id + '"]');
            return {
                id: input.id,
                checked: input.checked,
                label: label ? label.textContent.trim() : 'N/A',
            };
        });
    }
    """)

    print(f"\n  BHK default state: {json.dumps(bhk_state, indent=2)}")
    assert len(bhk_state) == 6, (
        f"Expected 6 BHK checkboxes, found {len(bhk_state)}"
    )

    expected_ids = [f"bhkFlatHouse_{i}" for i in range(6)]
    actual_ids = [b["id"] for b in bhk_state]
    assert actual_ids == expected_ids, (
        f"BHK IDs mismatch. Expected: {expected_ids}, Got: {actual_ids}"
    )
    print("[PASS] All 6 BHK checkboxes found.")


# =============================================================================
# TEST 6: Apply BHK filter - ONLY 2 BHK, Flat stays checked
# =============================================================================

async def test_06_apply_bhk_filter_2bhk_only():
    page = await _get_page()

    for i in range(6):
        checkbox = page.locator(f"input#bhkFlatHouse_{i}")
        label = page.locator(f"label[for='bhkFlatHouse_{i}']")

        if await checkbox.count() == 0:
            continue

        is_checked = await checkbox.is_checked()

        if i == 1:  # bhkFlatHouse_1 = 2 BHK
            if not is_checked:
                await label.evaluate("el => el.click()")
                await asyncio.sleep(0.3)
        else:
            if is_checked:
                await label.evaluate("el => el.click()")
                await asyncio.sleep(0.3)

    await asyncio.sleep(1)

    # VERIFY 1: Only 2 BHK is checked
    bhk_state = await page.evaluate("""
    () => {
        const inputs = document.querySelectorAll('input[name="bhkFlatHouse"]');
        return Array.from(inputs).map(input => {
            const label = document.querySelector('label[for="' + input.id + '"]');
            return {
                id: input.id,
                checked: input.checked,
                label: label ? label.textContent.trim() : 'N/A'
            };
        });
    }
    """)
    print(f"\n  BHK after filter: {json.dumps(bhk_state, indent=2)}")

    bhk_2 = next((c for c in bhk_state if c["id"] == "bhkFlatHouse_1"), None)
    assert bhk_2 is not None, "bhkFlatHouse_1 not found."
    assert bhk_2["checked"] is True, f"2 BHK should be checked. State: {bhk_state}"

    others = [c for c in bhk_state if c["id"] != "bhkFlatHouse_1" and c["checked"]]
    assert len(others) == 0, f"Other BHKs should be unchecked: {others}"

    # VERIFY 2: 'Flat' is STILL checked
    flat_checked = await page.evaluate(
        'document.getElementById("residential_0")?.checked'
    )
    assert flat_checked is True, (
        "BUG: 'Flat' (residential_0) got unchecked when toggling BHK! "
        "Selector is too broad - it's touching property type checkboxes."
    )

    print("[PASS] 2 BHK only selected. Flat still checked.")


# =============================================================================
# TEST 7: Apply Budget filter
# =============================================================================

async def test_07_apply_budget_filter():
    page = await _get_page()

    # Close property dropdown
    await page.mouse.click(0, 0)
    await asyncio.sleep(0.5)

    budget_dropdown = page.locator(".mb-search__budget .mb-search__title").first
    if await budget_dropdown.is_visible(timeout=2000):
        await budget_dropdown.evaluate("el => el.click()")
        await asyncio.sleep(1)

    min_input = page.locator("#budgetMin")
    assert await min_input.count() > 0, "#budgetMin not found."
    await min_input.evaluate("el => el.click()")
    await min_input.fill(str(config.MIN_BUDGET))

    max_input = page.locator("#budgetMax")
    assert await max_input.count() > 0, "#budgetMax not found."
    await max_input.evaluate("el => el.click()")
    await max_input.fill(str(config.MAX_BUDGET))
    await asyncio.sleep(0.5)

    min_val = await min_input.input_value()
    max_val = await max_input.input_value()
    assert min_val == str(config.MIN_BUDGET), f"Min: expected {config.MIN_BUDGET}, got '{min_val}'"
    assert max_val == str(config.MAX_BUDGET), f"Max: expected {config.MAX_BUDGET}, got '{max_val}'"
    print(f"\n[PASS] Budget: {min_val} - {max_val}")


# =============================================================================
# TEST 8: Click Search and verify URL
# =============================================================================

async def test_08_click_search_verify_url():
    page = await _get_page()

    # Close budget dropdown
    await page.mouse.click(0, 0)
    await asyncio.sleep(0.5)

    search_btn = page.locator(".mb-search__btn").first
    await search_btn.evaluate("el => el.click()")
    await page.wait_for_load_state("domcontentloaded")
    await asyncio.sleep(5)

    url = page.url.lower()
    print(f"\n  Final URL: {url}")

    assert "rent" in url or "for-rent" in url, f"No 'rent' in URL: {url}"
    assert "whitefield" in url, f"No 'whitefield' in URL: {url}"
    assert "bedroom=2" in url, f"No 'bedroom=2' in URL: {url}"
    assert "budgetmin=30000" in url, f"No 'budgetmin=30000' in URL: {url}"
    assert "budgetmax=40000" in url, f"No 'budgetmax=40000' in URL: {url}"

    print("[PASS] All filters verified in URL:")
    print(f"  Rent: OK | Whitefield: OK | 2 BHK: OK | Budget 30k-40k: OK")

    # Cleanup
    if "browser" in _page_holder:
        await _page_holder["browser"].close()
    if "pw" in _page_holder:
        await _page_holder["pw"].stop()
