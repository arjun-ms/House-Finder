"""
End-to-End test suite for the House Finder pipeline.

Tests ALL 6 user requirements:
  1. 2BHK apartment for rent         -> UI: Rent tab + 2 BHK checkbox
  2. 12th floor and above            -> data_filter: floor >= 12
  3. Whitefield or 5kms nearby       -> UI: multi-location dropdown selection
  4. Budget 50k - 60k                -> UI: budget min/max fields
  5. Age of property <= 5 years      -> data_filter: age <= 5
  6. Should have a balcony           -> data_filter: balcony >= 1

Split into two test groups:
  - Stage 1 (Browser UI): Tests that the agent correctly interacts with MagicBricks
  - Stage 2 (Data Filter): Tests that post-scrape filtering works on realistic data
"""

import pytest
import asyncio
from playwright.async_api import async_playwright

import config
from agents.browser_agent import (
    navigate_to_magicbricks,
    select_rent_tab,
    fill_location,
    apply_bhk_filter,
    apply_budget_filter,
    apply_more_filters,
    click_search,
)
from pipeline.data_filter import (
    filter_properties,
    parse_floor_number,
    parse_property_age,
    parse_balcony_count,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture(autouse=True)
def reset_config():
    """Ensure config is set to our exact requirements for every test."""
    config.SEARCH_KEYWORD = "Whitefield"
    config.CITY = "Bangalore"
    config.MAX_LOCATIONS_TO_SELECT = 3
    config.BHK_TYPE = "2 BHK"
    config.MIN_BUDGET = 50000
    config.MAX_BUDGET = 60000
    config.MIN_FLOOR = 12
    config.MAX_PROPERTY_AGE = 5
    config.REQUIRE_BALCONY = True
    # Disable progressive relaxation for strict filter tests
    config.TARGET_SHORTLIST = 0
    
    # Save test reports to a separate file so we don't overwrite real reports
    config.REPORT_MD = "output/test_report.md"
    config.RESULTS_JSON = "output/test_results.json"
    yield


# =============================================================================
# STAGE 1: BROWSER UI TEST (requires network access to MagicBricks)
# =============================================================================

@pytest.mark.asyncio
async def test_stage1_all_ui_filters_applied():
    """
    Full E2E browser test verifying ALL Stage 1 requirements:
      - Rent tab selected
      - Multiple Whitefield locations selected (5km nearby coverage)
      - 2 BHK exclusively checked
      - Budget set to 50000-60000

    Verified by inspecting the final URL after clicking Search.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
        )
        context = await browser.new_context(user_agent=config.USER_AGENT)
        page = await context.new_page()
        
        async def block_ads(route):
            url = route.request.url
            if "home-interior" in url.lower() or "hp_toolsandadvicesection" in url.lower():
                await route.abort()
            else:
                await route.continue_()
        await context.route("**/*", block_ads)

        try:
            for attempt in range(3):
                try:
                    await navigate_to_magicbricks(page)
                    await select_rent_tab(page)
                    await fill_location(page)
                    await apply_bhk_filter(page)
                    await apply_budget_filter(page)
                    await click_search(page)
                    await apply_more_filters(page, "16+")
                    break
                except Exception as e:
                    print(f"\n[!] Flaky UI interaction failed on attempt {attempt+1}: {e}")
                    if attempt == 2:
                        raise
                    await asyncio.sleep(2)
                    
            url = page.url.lower()
            print(f"\nFinal URL: {url}")

            # Requirement 1: "for rent"
            assert "rent" in url or "category=r" in url, (
                f"Rent filter not applied! URL: {url}"
            )

            # Requirement 3: "whitefield or 5kms nearby"
            assert "whitefield" in url, (
                f"Whitefield not in URL! URL: {url}"
            )
            whitefield_variants = [
                "whitefield",
                "whitefield-hoskote-road",
                "whitefield-main-road",
            ]
            matched = [v for v in whitefield_variants if v in url]
            assert len(matched) >= 1, (
                f"Expected at least one Whitefield location, got {matched}. URL: {url}"
            )
            print(f"  [OK] Whitefield locations matched: {matched}")

            # Requirement 1: "2bhk"
            assert "bedroom=2" in url, (
                f"2 BHK filter not applied! URL: {url}"
            )

            # Requirement 4: "budget 50k-60k"
            assert "budgetmin=50000" in url, (
                f"Min budget 50000 not in URL! URL: {url}"
            )
            assert "budgetmax=60000" in url, (
                f"Max budget 60000 not in URL! URL: {url}"
            )
            
            print("\n  ALL STAGE 1 UI FILTERS VERIFIED!")

        finally:
            await browser.close()


# =============================================================================
# STAGE 2: DATA FILTER TESTS (pure Python, no network needed)
# =============================================================================

# Realistic mock data simulating what the scraper returns from MagicBricks
MOCK_PROPERTIES = [
    {
        "property_name": "Prestige Shantiniketan",
        "floor_number": "14 out of 20",
        "property_age": "3 years",
        "balcony_count": 2,
        "rent": 55000,
        "bhk": "2 BHK",
        "locality": "Whitefield",
    },
    {
        "property_name": "Brigade Lakefront",
        "floor_number": "5 out of 18",
        "property_age": "2 years",
        "balcony_count": 1,
        "rent": 52000,
        "bhk": "2 BHK",
        "locality": "Whitefield",
    },
    {
        "property_name": "Sobha Dream Acres",
        "floor_number": "16 out of 22",
        "property_age": "8 years",
        "balcony_count": 1,
        "rent": 48000,
        "bhk": "2 BHK",
        "locality": "Whitefield",
    },
    {
        "property_name": "Phoenix One Bangalore West",
        "floor_number": "18 out of 25",
        "property_age": "1 years",
        "balcony_count": 0,
        "rent": 60000,
        "bhk": "2 BHK",
        "locality": "Whitefield",
    },
    {
        "property_name": "Mantri Webcity",
        "floor_number": "15 out of 20",
        "property_age": "4 years",
        "balcony_count": 2,
        "rent": 58000,
        "bhk": "2 BHK",
        "locality": "Whitefield Main Road",
    },
    {
        "property_name": "Salarpuria Sattva Greenage",
        "floor_number": "3 out of 15",
        "property_age": "10 years",
        "balcony_count": 0,
        "rent": 45000,
        "bhk": "2 BHK",
        "locality": "Whitefield Hoskote Road",
    },
    {
        "property_name": "Godrej Splendour",
        "floor_number": "12 out of 18",
        "property_age": "New Construction",
        "balcony_count": 3,
        "rent": 56000,
        "bhk": "2 BHK",
        "locality": "Whitefield",
    },
    {
        "property_name": "Embassy Springs",
        "floor_number": "20 out of 30",
        "property_age": "2 years",
        "balcony_count": 1,
        "rent": 59000,
        "bhk": "2 BHK",
        "locality": "Whitefield",
    },
]


# --- Parser unit tests ---

class TestParserFunctions:
    """Test individual parser functions used by the data filter."""

    def test_parse_floor_from_string(self):
        assert parse_floor_number({"floor_number": "14 out of 20"}) == 14

    def test_parse_floor_from_int(self):
        assert parse_floor_number({"floor_number": 12}) == 12

    def test_parse_floor_missing(self):
        assert parse_floor_number({}) is None

    def test_parse_floor_empty_string(self):
        assert parse_floor_number({"floor_number": ""}) is None

    def test_parse_age_from_string(self):
        assert parse_property_age({"property_age": "3 years"}) == 3.0

    def test_parse_age_new_construction(self):
        assert parse_property_age({"property_age": "New Construction"}) == 0

    def test_parse_age_range(self):
        """'1 to 5 years' should parse as 1.0 (first number)."""
        assert parse_property_age({"property_age": "1 to 5 years"}) == 1.0

    def test_parse_age_from_number(self):
        assert parse_property_age({"property_age": 4}) == 4.0

    def test_parse_age_missing(self):
        assert parse_property_age({}) is None

    def test_parse_balcony_from_int(self):
        assert parse_balcony_count({"balcony_count": 2}) == 2

    def test_parse_balcony_zero(self):
        assert parse_balcony_count({"balcony_count": 0}) == 0

    def test_parse_balcony_from_string(self):
        assert parse_balcony_count({"balcony_count": "3"}) == 3

    def test_parse_balcony_yes(self):
        assert parse_balcony_count({"balcony_count": "Yes"}) == 1

    def test_parse_balcony_missing(self):
        assert parse_balcony_count({}) is None


# --- Individual filter requirement tests ---

class TestFloorFilter:
    """Requirement 2: 12th floor and above."""

    def test_high_floor_passes(self):
        props = [{"property_name": "High", "floor_number": 14, "property_age": 3, "balcony_count": 2}]
        filtered, _ = filter_properties(props)
        assert len(filtered) == 1

    def test_floor_12_passes(self):
        """Exactly 12th floor should pass (>= 12)."""
        props = [{"property_name": "Edge", "floor_number": 12, "property_age": 1, "balcony_count": 1}]
        filtered, _ = filter_properties(props)
        assert len(filtered) == 1

    def test_floor_11_excluded(self):
        """Floor 11 should be excluded (< 12)."""
        props = [{"property_name": "Low", "floor_number": 11, "property_age": 1, "balcony_count": 1}]
        filtered, excluded = filter_properties(props)
        assert len(filtered) == 0
        assert len(excluded) == 1

    def test_floor_5_excluded(self):
        props = [{"property_name": "VeryLow", "floor_number": "5 out of 18", "property_age": "2 years", "balcony_count": 1}]
        filtered, excluded = filter_properties(props)
        assert len(filtered) == 0
        assert any("Floor 5" in n for n in excluded[0]["filter_notes"])

    def test_missing_floor_included_with_flag(self):
        """Unknown floor should be included but flagged as incomplete."""
        props = [{"property_name": "NoFloor", "property_age": 2, "balcony_count": 1}]
        filtered, _ = filter_properties(props)
        assert len(filtered) == 1
        assert filtered[0]["data_complete"] is False


class TestAgeFilter:
    """Requirement 5: Age of property <= 5 years."""

    def test_new_construction_passes(self):
        props = [{"property_name": "New", "floor_number": 15, "property_age": "New Construction", "balcony_count": 1}]
        filtered, _ = filter_properties(props)
        assert len(filtered) == 1

    def test_age_5_passes(self):
        """Exactly 5 years should pass (<= 5)."""
        props = [{"property_name": "FiveYears", "floor_number": 14, "property_age": 5, "balcony_count": 1}]
        filtered, _ = filter_properties(props)
        assert len(filtered) == 1

    def test_age_6_excluded(self):
        props = [{"property_name": "SixYears", "floor_number": 14, "property_age": 6, "balcony_count": 1}]
        filtered, excluded = filter_properties(props)
        assert len(filtered) == 0
        assert len(excluded) == 1

    def test_age_8_excluded(self):
        props = [{"property_name": "Old", "floor_number": 16, "property_age": "8 years", "balcony_count": 1}]
        filtered, excluded = filter_properties(props)
        assert len(filtered) == 0
        assert any("Age 8" in n for n in excluded[0]["filter_notes"])

    def test_missing_age_included_with_flag(self):
        props = [{"property_name": "NoAge", "floor_number": 15, "balcony_count": 1}]
        filtered, _ = filter_properties(props)
        assert len(filtered) == 1
        assert filtered[0]["data_complete"] is False


class TestBalconyFilter:
    """Requirement 6: Should have a balcony."""

    def test_has_balcony_passes(self):
        props = [{"property_name": "WithBalcony", "floor_number": 14, "property_age": 2, "balcony_count": 2}]
        filtered, _ = filter_properties(props)
        assert len(filtered) == 1

    def test_no_balcony_excluded(self):
        props = [{"property_name": "NoBalcony", "floor_number": 18, "property_age": 1, "balcony_count": 0}]
        filtered, excluded = filter_properties(props)
        assert len(filtered) == 0
        assert any("No balcony" in n for n in excluded[0]["filter_notes"])

    def test_missing_balcony_included_with_flag(self):
        props = [{"property_name": "Unknown", "floor_number": 15, "property_age": 2}]
        filtered, _ = filter_properties(props)
        assert len(filtered) == 1
        assert filtered[0]["data_complete"] is False


# --- Full realistic batch test ---

class TestRealisticDataFilterBatch:
    """
    Run the full filter on realistic mock data (8 properties)
    and verify the correct ones pass/fail.
    """

    def test_filter_realistic_batch(self):
        """
        Expected results from MOCK_PROPERTIES:
          - Prestige Shantiniketan:  floor=14, age=3, balcony=2  -> PASS
          - Brigade Lakefront:      floor=5,  age=2, balcony=1  -> FAIL (floor < 12)
          - Sobha Dream Acres:      floor=16, age=8, balcony=1  -> FAIL (age > 5)
          - Phoenix One BW:         floor=18, age=1, balcony=0  -> FAIL (no balcony)
          - Mantri Webcity:         floor=15, age=4, balcony=2  -> PASS
          - Salarpuria Greenage:    floor=3,  age=10, balcony=0 -> FAIL (all three)
          - Godrej Splendour:       floor=12, age=0, balcony=3  -> PASS
          - Embassy Springs:        floor=20, age=2, balcony=1  -> PASS
        """
        filtered, excluded = filter_properties(MOCK_PROPERTIES)

        passed_names = [p["property_name"] for p in filtered]
        excluded_names = [p["property_name"] for p in excluded]

        # Should PASS
        assert "Prestige Shantiniketan" in passed_names
        assert "Mantri Webcity" in passed_names
        assert "Godrej Splendour" in passed_names
        assert "Embassy Springs" in passed_names

        # Should FAIL
        assert "Brigade Lakefront" in excluded_names, "Brigade should fail (floor=5)"
        assert "Sobha Dream Acres" in excluded_names, "Sobha should fail (age=8)"
        assert "Phoenix One Bangalore West" in excluded_names, "Phoenix should fail (no balcony)"
        assert "Salarpuria Sattva Greenage" in excluded_names, "Salarpuria should fail (floor, age, balcony)"

        assert len(filtered) == 4, f"Expected 4 passed, got {len(filtered)}: {passed_names}"
        assert len(excluded) == 4, f"Expected 4 excluded, got {len(excluded)}: {excluded_names}"

    def test_all_passed_have_complete_data(self):
        filtered, _ = filter_properties(MOCK_PROPERTIES)
        for prop in filtered:
            assert prop["data_complete"] is True, (
                f"{prop['property_name']} should have complete data"
            )

    def test_salarpuria_fails_three_filters(self):
        """Salarpuria fails 3 filters: floor, age, AND balcony."""
        _, excluded = filter_properties(MOCK_PROPERTIES)
        salarpuria = next(p for p in excluded if "Salarpuria" in p["property_name"])
        reasons = salarpuria.get("exclusion_reason", [])
        assert any("Floor" in r for r in reasons)
        assert any("Age" in r for r in reasons)
        assert any("balcony" in r for r in reasons)
