# House Finder - Domain Glossary

> Pure domain language. No implementation details.

## Terms

- **Browser Agent**: The automated Playwright script that interacts with MagicBricks as a human would - typing, clicking, filling forms, navigating pages, and extracting data from the visible UI.

- **Stage 1 Filtering**: Filters applied via the MagicBricks search form UI (Rent, 2BHK, Whitefield localities, budget 50k-60k). These are the filters the website natively supports.

- **Stage 2 Filtering**: Programmatic filters applied after scraping individual property detail pages. Covers criteria MagicBricks doesn't expose as search filters: floor >= 12, age of property <= 5 years, has balcony.

- **Property Detail Page**: The individual MagicBricks listing page for a single property. Contains full data: floor number, property age, balcony count, amenities, builder name, etc. The browser agent must click into each listing to reach this page.

- **Search Results Page**: The MagicBricks page showing multiple property cards after a search. Contains limited data (price, location, area). The agent collects listing URLs from here, paginating until MAX_LISTINGS_TO_SCRAPE is reached.

- **Shortlisted Properties**: The ~10 properties that survive both Stage 1 and Stage 2 filtering. These are passed to the LLM for ranking.

- **LLM Recommender**: The Gemini 2.0 Flash model that receives all shortlisted properties as structured JSON, scores them on weighted criteria, and returns a ranked list with the top 3 and a best pick with reasoning.

- **Listing**: A single rental property entry on MagicBricks. Used interchangeably with "property" in this project.

- **Whitefield Radius**: The search area defined by typing "Whitefield" in MagicBricks and selecting all dropdown options containing the keyword. Approximates the "Whitefield or 5km nearby" requirement.
