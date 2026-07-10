# Product Requirements Document (PRD): House Finder

## 1. Overview
House Finder is an automated Playwright-based browser agent designed to streamline the apartment hunting process on MagicBricks. Instead of manually scrolling, filtering, and evaluating hundreds of listings, the system acts as a "human" user—interacting with the UI, extracting data, and employing an AI (Google Gemini 2.0 Flash) to evaluate, rank, and present the top 3 rental properties in a structured, actionable format.

## 2. Target Audience & Use Case
- **Target User:** Individuals looking to rent premium 2BHK apartments in specific localities (e.g., Whitefield, Bangalore) with strict preferences (high floor, new property, specific budget).
- **Core Problem:** Real estate platforms like MagicBricks do not expose complex, multi-variable filters natively (e.g., "Must be on the 12th floor or higher" or "Must be less than 5 years old"). Manual discovery is tedious and time-consuming.
- **Solution:** A dual-stage filtering pipeline paired with an LLM-based recommender that evaluates properties similarly to a human decision-maker.

## 3. Product Capabilities

### 3.1. Browser Automation (The "Agent")
- Must launch a visible (headed) Chromium browser.
- Must navigate to MagicBricks.com.
- Must emulate human-like interactions (typing, clicking, filling forms, and pausing to avoid bot detection).
- Must record the browser session as a video file for auditing and debugging.

### 3.2. Stage 1 Filtering (UI-Level)
The agent will utilize the native MagicBricks search form to apply primary constraints:
- **Location:** Whitefield (and surrounding radius based on dropdown options).
- **Property Type:** Rent.
- **BHK Type:** 2 BHK.
- **Budget:** Rs. 50,000 to Rs. 60,000 per month.

### 3.3. Stage 2 Filtering (Programmatic Level)
After scraping the initial search results (up to 40 listings), the agent must visit individual "Property Detail Pages" to apply strict, programmatic constraints that MagicBricks does not natively support as search filters:
- **Minimum Floor:** >= 12th Floor.
- **Maximum Property Age:** <= 5 Years old.
- **Balcony Requirement:** Must have at least 1 balcony.
- *Goal:* Narrow down the 40 raw listings to approximately 10 shortlisted properties.

### 3.4. AI-Powered Recommendation (LLM Level)
The shortlisted properties will be passed as a structured JSON payload to the LLM Recommender (Gemini 2.0 Flash). The LLM will rank the properties based on the following weighted criteria (summing to 1.0):
1. **Rent Value (30%):** Value for money considering rent vs. area, furnishing status, etc.
2. **Floor Preference (25%):** Higher floors are heavily preferred (all must already satisfy the >= 12 baseline).
3. **Property Age (20%):** Newer properties are preferred.
4. **Location Quality (15%):** Proximity to the center of Whitefield.
5. **Amenities (10%):** Quality/quantity of balconies, gym, parking, etc.

*Output:* The LLM will select the Top 3 properties and identify a single "Best Pick," accompanied by detailed reasoning.

### 3.5. Reporting & Output
The system must generate three formats of the final output:
1. `results.json`: Complete, machine-readable dataset including all scraped properties, filter statuses, and the raw LLM rankings.
2. `report.md`: A clean, human-readable Markdown summary of the top 3 picks and the reasoning.
3. `report.html`: A visual, styled HTML report for the best user experience.

## 4. Key Components & Architecture

- **Browser Agent (`browser_agent.py`):** Handles all Playwright interactions, pagination, and data extraction.
- **Data Filter (`data_filter.py`):** Executes Stage 2 programmatic filtering logic on the extracted raw property data.
- **LLM Recommender (`llm_recommender.py`):** Connects to the Google Gemini API to analyze the shortlist and generate rankings based on configured weights.
- **Report Generator (`report_generator.py`):** Transforms the LLM's output into the required JSON, MD, and HTML formats.

## 5. Non-Functional Requirements & Constraints
- **Timeouts:** 
  - Page Load Timeout: 30 seconds.
  - Property Detail Page Timeout: 15 seconds.
- **Delays:** Random delays between 2 to 5 seconds for page navigations to mimic human behavior.
- **Environment Constraints:** Requires Python 3.10+ and a valid Google Gemini API key.
- **Execution Time:** The end-to-end pipeline (scraping 40 listings + LLM evaluation) is expected to take approximately 5-8 minutes.
