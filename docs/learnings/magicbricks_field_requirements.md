# MagicBricks Field Requirements & Scraping Realities

**Date:** July 12, 2026
**Topic:** Understanding which property data fields are mandatory vs optional on the MagicBricks platform, and how this impacts the scraper pipeline.

## Overview
When scraping user-generated content from real estate platforms like MagicBricks, it is critical to understand the platform's data entry rules. If a field is optional for the poster (the broker or owner), it will frequently be missing from the page's HTML, leading to `None` values in the scraper.

This document outlines the three core metrics we rely on, their strictness on the platform, and how our `data_filter.py` pipeline is built to handle them gracefully.

---

## 1. Floor Details: STRICTLY REQUIRED
- **Platform Reality:** When creating a property listing, the floor configuration (e.g., "3 out of 5 floors") is a mandatory dropdown field. 
- **Scraping Consistency:** High. We rarely, if ever, see a standard apartment property where the floor number is entirely missing from the DOM.
- **Pipeline Handling:** Because we can rely on this field existing, our pipeline enforces strict deletion on it. If `config.MIN_FLOOR = 5` and the scraper pulls a property on Floor 3, it is instantly discarded.

## 2. Age of Property (Age of Construction): OPTIONAL
- **Platform Reality:** This field is entirely optional for the person creating the listing. Many brokers skip it intentionally (to avoid scaring off buyers with old building ages) or simply to save time filling out the form. 
- **Scraping Consistency:** Low. It is frequently completely missing from the `propertyDetails` table.
- **Pipeline Handling:** Because it is routinely missing, the pipeline treats missing values with "forgiveness". If the Age is missing, the scraper does not crash. Instead, it logs it as `unknown Yrs`, explicitly passes this fact to the LLM, and **keeps** the property in the running.

## 3. Balcony Count: OPTIONAL
- **Platform Reality:** Balcony is a checkbox/number field in the listing form. If a broker does not explicitly check "1 Balcony" or select a number, MagicBricks will not render the Balcony label anywhere on the search page or the deep details page.
- **Scraping Consistency:** Medium-Low. Many properties physically have balconies, but the listing agent simply didn't input it on the website.
- **Pipeline Handling:** The pipeline treats this exactly like the Age field. If `config.REQUIRE_BALCONY = True`:
  - If the page explicitly says `0 Balconies`, the property is **deleted**.
  - If the page explicitly says `1+ Balconies`, it passes.
  - If the field is **missing entirely**, the script assumes it might have been lazy data entry, flags it as `Balcony: unknown (included with flag)`, and **keeps** it for the LLM to review.

## Conclusion
The data pipeline is perfectly tuned to the realities of MagicBricks. We enforce strict deterministic filters (like deleting 3rd-floor apartments) on fields that MagicBricks guarantees, and we apply "forgiving" logic to optional fields to ensure we don't accidentally delete incredible properties just because a broker forgot to check a box.
