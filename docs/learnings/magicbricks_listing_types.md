# MagicBricks Listing Types: Individual Flats vs Builder Projects

When scraping MagicBricks (and similar Indian real estate portals), it is critical to understand the architectural difference between how they render different types of listings. 

This difference dictates whether strict data extraction (like `property_age` and `floor_number`) will succeed or return `None`.

## 1. Individual Listings (Single Flat)
* **Target:** A single, specific apartment (e.g., Tower B, Flat 1402).
* **Uploader:** Individual landlords, homeowners, or brokers.
* **URL Structure:** Typically contains `/propertyDetails/` and ends with `&id=...` (e.g., `...&id=4d423834333336383335`).
* **Data Availability (DOM):** MagicBricks forces individual uploaders to fill out a strict, standardized form. Because of this, the final rendered webpage includes a highly structured **"Facts" table**.
* **Extraction:** Scrapers can easily target `.mb-ldp__dtls__body__list--item` to extract precise key-value pairs like:
  * `Carpet Area: 956 sqft`
  * `Floor: 14 out of 20`
  * `Age of Construction: Less than 5 years`

## 2. Builder Project Pages (Entire Society)
* **Target:** An entire residential complex or society (e.g., Assetz Marq, Brigade Cosmopolis).
* **Uploader:** Massive Tier-1 real estate developers.
* **URL Structure:** Contains `-pdpid-` (Project Detail Page ID) (e.g., `...-pdpid-4d4235303730313131`).
* **Data Availability (DOM):** Because a single project might encompass 15 different towers built over 10 years, the webpage **deliberately omits specific "Age" or "Floor" data**. It is a marketing brochure, not a flat specification sheet.
* **Extraction:** The structured "Facts" table is completely missing. Instead, the page relies on generic marketing bullet points (`.mb-ldp__more-dtl__list`) such as:
  * *"Spread across 22 acres"*
  * *"Offers 2BHK, 3BHK luxury configurations"*
* **Why this breaks scrapers:** When a scraper navigates to a `pdpid` page looking for exact floor numbers or age, it will parse the DOM and correctly return `None` because the uploader literally did not write that data into the page.

### The Search Results Paradox
Why do project pages show up in strict search results if they don't list the data?

MagicBricks' backend algorithm *knows* the age of the project. If a user filters by `Age < 5 years`, MagicBricks will inject these projects into the Search Results Page (SRP). However, once the scraper navigates away from the SRP and clicks into the Project Detail Page (PDP), the specific age/floor data disappears, replaced by the generic marketing copy. 

**Architectural Takeaways:**
1. If strict data like Floor and Age is mandatory, scrapers must either:
   - Explicitly filter out `pdpid` URLs during the collection phase (which may severely limit inventory in premium tiers).
   - Extract the `Age` and `Floor` directly from the smaller summary cards on the Search Results Page (SRP) *before* navigating into the detail page, as the SRP cards sometimes expose the backend data.
2. For project pages, fallback logic must be implemented to cleanly handle `None` values (e.g., displaying `N/A` or `UI Filtered`) without crashing the pipeline.
