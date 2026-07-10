# Issue 3: Implement Stage 2 Programmatic Filtering & Data Extraction

## Description
After obtaining search results, the agent must scrape property listings up to a maximum limit and apply strict programmatic filters (`data_filter.py`) for criteria that the MagicBricks UI does not support.

## Requirements
- Paginate through the search results until `MAX_LISTINGS_TO_SCRAPE` (e.g., 40) properties are collected.
- Click into each individual property detail page.
- Set a 15-second timeout for property detail page elements.
- Extract fields: Floor number, Property Age, Balcony presence, Amenities, Builder, and Rent.
- Filter out properties that do not meet the following criteria:
  - Minimum Floor >= 12.
  - Property Age <= 5 years.
  - Balcony count >= 1.
- Target a shortlist of approximately 10 properties.

## Acceptance Criteria
- The system correctly loops through and scrapes data from detail pages.
- The programmatic filter successfully drops listings that fail the strict floor, age, or balcony criteria.
- The output is a clean JSON array of shortlisted properties.
