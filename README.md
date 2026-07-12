# House Finder - AI Property Recommendation Pipeline

A highly robust, 3-phase AI automation pipeline that searches MagicBricks for 2BHK rental apartments in Bangalore, extracts property details directly from the DOM, strictly filters them based on programmatic heuristics, and uses a Google Gemini Cognitive Engine to rank and recommend the top properties.

## View the demo video below



## What It Does (The 3-Phase Pipeline)

1. **Phase 1: Deterministic Fast-Path Scraping (Playwright)**
   - Launches a headless/headed browser and navigates to MagicBricks.
   - Interacts dynamically with the UI (types location, handles dropdowns, selects BHK, sets budget).
   - Scrapes property listings and executes "Deep Scraping" on individual pages to pull hidden text.
2. **Phase 2: Strict Heuristic Filtering (Python)**
   - Applies strict criteria that the MagicBricks UI fails to enforce.
   - Filters out properties below the minimum floor (e.g., `< 5th floor`).
   - Filters out older properties (e.g., `> 15 years`).
   - Handles data quirks natively (e.g., dropping mega-project `-pdpid-` pages when running in non-Whitefield areas).
3. **Phase 3: Cognitive Ranking Engine (Gemini)**
   - Sends the sanitized, filtered JSON data to the LLM.
   - Uses Gemini to score properties based on narrative descriptions, hidden amenities, and overall value.
   - Generates polished machine-readable (JSON) and human-readable (Markdown & HTML) reports.

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

All search criteria and behavior constants are in `src/config.py`:

```python
# Key settings you might want to tweak
SEARCH_KEYWORD = "Whitefield, Bangalore"
MAX_LISTINGS_TO_SCRAPE = 30   # How many listings to scrape
MIN_FLOOR = 5                 # Minimum floor number
MAX_PROPERTY_AGE = 15         # Max property age in years
MIN_BUDGET = 30000            # Monthly rent min
MAX_BUDGET = 40000            # Monthly rent max
```

## Usage

**Run the Main Pipeline:**
```bash
python src/main.py
```

**Run the Koramangala Test Script:**
This repository includes a dedicated test script proving the scraper's ability to extract pure, standalone flats (bypassing the mega-projects that typically dominate Whitefield searches).
```bash
python scripts/run_koramangala.py
```

## Output

After running, check the `output/` directory:

| File | Description |
|------|-------------|
| `results.json` | Complete data - all scraped properties, filters applied, LLM rankings |
| `report.md` | Clean markdown report with top 3 picks and reasoning |
| `min_5_report.html` | Visual HTML report - open in browser for best experience |

## Project Structure

```text
House Finder/
|-- src/
|   |-- config.py               # Tweakable constants
|   |-- main.py                 # Entry point - orchestrates pipeline
|   |-- agents/
|       |-- browser_agent.py    # Playwright deterministic scraper
|       |-- smart_browser_agent.py # LangChain implementation (bypassed for speed)
|       |-- agent_tools.py      # DOM inspection tools for AI
|   |-- pipeline/
|       |-- data_filter.py      # Stage 2 programmatic filtering
|       |-- llm_recommender.py  # Gemini API integration
|       |-- report_generator.py # JSON + MD + HTML output generation
|
|-- scripts/
|   |-- run_koramangala.py      # Test script for non-project data extraction
|
|-- docs/
|   |-- PRD.md                  # Project Requirements Document
|   |-- learnings/              # Edge-case documentation & Mermaid flowcharts
|
|-- output/                     # Generated reports
|-- requirements.txt            # Python dependencies
|-- README.md                   # This file
```

## Documentation & Edge Cases

Please view `docs/learnings/` for deep-dive documentation on how this pipeline handles specific real-world data quirks:
- `magicbricks_field_requirements.md`: Explains why `Floor` is strictly enforced but `Age`/`Balcony` are heavily relaxed due to lazy broker data entry.
- `magicbricks_location_expansion.md`: Explains why locations like "Varthur" and "KR Puram" legitimately appear in "Whitefield" searches due to MagicBricks' algorithmic boundary expansion.
- `flowchart.mmd`: The Mermaid architecture diagram detailing the execution flow.
