"""
Data Filter - Stage 2 programmatic filtering of scraped property data.

Applies filters that MagicBricks doesn't support in its search UI:
- Floor number >= MIN_FLOOR
- Property age <= MAX_PROPERTY_AGE
- Has balcony (if REQUIRE_BALCONY is True)

Properties with missing data for filter fields are INCLUDED but flagged.
"""

import re
import config


def parse_floor_number(property_data: dict) -> int | None:
    """Extract floor number from property data."""
    floor = property_data.get("floor_number")
    if isinstance(floor, (int, float)):
        return int(floor)

    # Try parsing from text if it's a string
    if isinstance(floor, str):
        numbers = re.findall(r"\d+", floor)
        if numbers:
            return int(numbers[0])

    return None


def parse_property_age(property_data: dict) -> float | None:
    """Extract property age in years from property data."""
    age = property_data.get("property_age")
    if isinstance(age, (int, float)):
        return float(age)

    if isinstance(age, str):
        age_lower = age.lower()
        # Handle "New" or "Under Construction"
        if "new" in age_lower or "under construction" in age_lower:
            return 0
        # Handle "X years" or "X-Y years"
        numbers = re.findall(r"[\d.]+", age)
        if numbers:
            return float(numbers[0])

    return None


def parse_balcony_count(property_data: dict) -> int | None:
    """Extract balcony count from property data."""
    balcony = property_data.get("balcony_count")
    if isinstance(balcony, (int, float)):
        return int(balcony)

    if isinstance(balcony, str):
        numbers = re.findall(r"\d+", balcony)
        if numbers:
            return int(numbers[0])
        # "Yes" means at least 1
        if "yes" in balcony.lower():
            return 1

    return None


def filter_properties(properties: list[dict]) -> tuple[list[dict], list[dict]]:
    """
    Apply Stage 2 filters to scraped properties.

    Filtering strategy:
    - Properties with data that FAILS a filter are EXCLUDED
    - Properties with MISSING data for a filter field are INCLUDED but flagged
    - If not enough properties pass, filters are relaxed progressively

    Returns filtered list with 'data_complete' and 'filter_notes' flags added.
    """
    print(f"\n[*] Stage 2 Filtering: {len(properties)} properties...")
    print(f"    Criteria: Floor >= {config.MIN_FLOOR}, "
          f"Age <= {config.MAX_PROPERTY_AGE} years, "
          f"Balcony: {'Required' if config.REQUIRE_BALCONY else 'Optional'}")

    filtered = []
    excluded = []

    for prop in properties:
        notes = []
        should_include = True

        # --- Floor Filter ---
        floor = parse_floor_number(prop)
        if floor is not None:
            if floor < config.MIN_FLOOR:
                should_include = False
                notes.append(f"Floor {floor} < {config.MIN_FLOOR} (excluded)")
            else:
                notes.append(f"Floor {floor} (OK)")
        else:
            notes.append("Floor: unknown (included with flag)")

        # --- Budget Filter ---
        price = prop.get("price")
        if isinstance(price, (int, float)):
            if price < config.MIN_BUDGET or price > config.MAX_BUDGET:
                should_include = False
                notes.append(f"Price {price} out of range (excluded)")
            else:
                notes.append(f"Price {price} (OK)")
        else:
            notes.append("Price: unknown (included with flag)")

        # --- Property Age Filter ---
        age = parse_property_age(prop)
        if age is not None:
            if age > config.MAX_PROPERTY_AGE:
                should_include = False
                notes.append(f"Age {age} years > {config.MAX_PROPERTY_AGE} (excluded)")
            else:
                notes.append(f"Age {age} years (OK)")
        else:
            notes.append("Age: unknown (included with flag)")

        # --- Balcony Filter ---
        if config.REQUIRE_BALCONY:
            balcony = parse_balcony_count(prop)
            if balcony is not None:
                if balcony < 1:
                    should_include = False
                    notes.append("No balcony (excluded)")
                else:
                    notes.append(f"Balcony: {balcony} (OK)")
            else:
                notes.append("Balcony: unknown (included with flag)")

        # Determine data completeness
        data_complete = all([
            parse_floor_number(prop) is not None,
            parse_property_age(prop) is not None,
            parse_balcony_count(prop) is not None,
        ])

        prop_enriched = {
            **prop,
            "data_complete": data_complete,
            "filter_notes": notes,
        }

        if should_include:
            filtered.append(prop_enriched)
        else:
            prop_enriched["exclusion_reason"] = [n for n in notes if "excluded" in n]
            excluded.append(prop_enriched)

    print(f"[*] After strict filtering: {len(filtered)} passed, {len(excluded)} excluded")

    # Progressive relaxation if not enough properties
    if len(filtered) < config.TARGET_SHORTLIST:
        print(f"\n[!] Only {len(filtered)} properties passed. "
              f"Need {config.TARGET_SHORTLIST}. Relaxing filters...")

        # Round 1: Re-include properties excluded ONLY by balcony
        if len(filtered) < config.TARGET_SHORTLIST and config.REQUIRE_BALCONY:
            for prop in excluded[:]:
                reasons = prop.get("exclusion_reason", [])
                if all("balcony" in r.lower() for r in reasons):
                    prop["filter_notes"].append("RELAXED: Balcony requirement waived")
                    filtered.append(prop)
                    excluded.remove(prop)
            print(f"    After relaxing balcony: {len(filtered)} properties")

        # Round 2: Re-include properties excluded ONLY by age
        if len(filtered) < config.TARGET_SHORTLIST:
            for prop in excluded[:]:
                reasons = prop.get("exclusion_reason", [])
                if all("age" in r.lower() for r in reasons):
                    prop["filter_notes"].append("RELAXED: Age requirement waived")
                    filtered.append(prop)
                    excluded.remove(prop)
            print(f"    After relaxing age: {len(filtered)} properties")

        # Round 3: Re-include properties excluded ONLY by floor
        if len(filtered) < config.TARGET_SHORTLIST:
            for prop in excluded[:]:
                reasons = prop.get("exclusion_reason", [])
                if all("floor" in r.lower() for r in reasons):
                    prop["filter_notes"].append("RELAXED: Floor requirement waived")
                    filtered.append(prop)
                    excluded.remove(prop)
            print(f"    After relaxing floor: {len(filtered)} properties")

    # Sort: complete data first, then by property name
    filtered.sort(key=lambda p: (not p["data_complete"], p.get("property_name") or "ZZZ"))

    print(f"\n[*] Final filtered list: {len(filtered)} properties")
    for i, prop in enumerate(filtered, 1):
        name = prop.get("property_name") or "Unknown"
        complete = "Complete" if prop["data_complete"] else "Incomplete"
        print(f"    {i}. {name[:40]} ({complete})")

    return filtered, excluded
