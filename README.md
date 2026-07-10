# House Finder - Browser Agent for Property Recommendation

A Playwright-based browser agent that searches MagicBricks for 2BHK rental apartments in Whitefield, Bangalore, scrapes property details from the UI, and uses Google Gemini 2.0 Flash to recommend the top 3 properties.

## What It Does

1. **Launches a visible browser** and navigates to MagicBricks
2. **Fills the search form** - types location, selects BHK, sets budget (real UI interaction, no API calls)
3. **Collects listings** from search results, paginating until enough are found
4. **Clicks into each property page** to scrape detailed data (floor, age, balcony, amenities, etc.)
5. **Filters programmatically** - applies criteria the website doesn't support (floor >= 12, age <= 5 years, has balcony)
6. **Sends data to Gemini AI** for intelligent ranking based on weighted scoring criteria
7. **Generates reports** - JSON (machine-readable), Markdown (human-readable), and HTML (visual)
8. **Records the browser session** as a video file

## Setup

### Prerequisites

- Python 3.10+
- Google Gemini API key ([Get one here](https://aistudio.google.com/apikey))

### Installation

```bash
# Clone the repo
git clone <repo-url>
cd "House Finder"

# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Install Playwright browser
playwright install chromium

# Set up API key
copy .env.example .env
# Edit .env and paste your Gemini API key
```

### Configuration

All search criteria and behavior constants are in [`config.py`](config.py):

```python
# Key settings you might want to tweak
MAX_LISTINGS_TO_SCRAPE = 40   # How many listings to scrape
MIN_FLOOR = 12                # Minimum floor number
MAX_PROPERTY_AGE = 5          # Max property age in years
MIN_BUDGET = 50000            # Monthly rent min
MAX_BUDGET = 60000            # Monthly rent max
```

## Usage

```bash
python main.py
```

The agent will:
- Open a visible Chrome browser
- Interact with MagicBricks search form
- Scrape property details (takes ~5-8 minutes)
- Generate recommendations
- Save outputs to `output/` directory

## Output

After running, check the `output/` directory:

| File | Description |
|------|-------------|
| `results.json` | Complete data - all scraped properties, filters applied, LLM rankings |
| `report.md` | Clean markdown report with top 3 picks and reasoning |
| `report.html` | Visual HTML report - open in browser for best experience |
| `*.webm` | Recorded browser session video |

## Project Structure

```
House Finder/
|-- config.py               # All tweakable constants
|-- main.py                 # Entry point - orchestrates pipeline
|-- browser_agent.py        # Playwright browser automation
|-- data_filter.py          # Stage 2 programmatic filtering
|-- llm_recommender.py      # Gemini API integration
|-- report_generator.py     # JSON + MD + HTML output generation
|-- requirements.txt        # Python dependencies
|-- .env.example            # API key template
|-- .env                    # Your API key (gitignored)
|-- CONTEXT.md              # Domain glossary
|-- README.md               # This file
|-- output/                 # Generated reports and video
```

## Architecture

```
MagicBricks.com
       |
       v
[Browser Agent]  -->  Fill form, click, navigate, scrape
       |
       v
[Raw Property Data]  -->  40 listings with 14 fields each
       |
       v
[Stage 2 Filter]  -->  Floor >= 12, Age <= 5yr, Has Balcony
       |
       v
[Filtered Properties]  -->  ~10-15 properties
       |
       v
[Gemini 2.0 Flash]  -->  Score, rank, pick top 3
       |
       v
[Reports]  -->  JSON + Markdown + HTML
```

## Search Criteria

| Criteria | Value | Filter Stage |
|----------|-------|-------------|
| Property Type | 2BHK Apartment for Rent | Stage 1 (UI) |
| Location | Whitefield, Bangalore | Stage 1 (UI) |
| Budget | Rs 50,000 - 60,000/month | Stage 1 (UI) |
| Floor | 12th and above | Stage 2 (Code) |
| Property Age | 5 years or newer | Stage 2 (Code) |
| Balcony | Required | Stage 2 (Code) |
