"""
Configuration constants for the House Finder browser agent.
Edit these values to tweak search criteria and agent behavior.
"""

# =============================================================================
# SEARCH CRITERIA (Stage 1 - Applied via MagicBricks UI)
# =============================================================================

SEARCH_KEYWORD = "Whitefield"
CITY = "Bangalore"
MAX_LOCATIONS_TO_SELECT = 3
BHK_TYPE = "2 BHK"
MIN_BUDGET = 30000
MAX_BUDGET = 40000
PROPERTY_TYPE = "Rent"

# =============================================================================
# FILTER CRITERIA (Stage 2 - Applied programmatically after scraping)
# =============================================================================

MIN_FLOOR = 5              # 12th floor and above
MAX_PROPERTY_AGE = 15        # Property age <= 5 years
REQUIRE_BALCONY = True      # Must have at least 1 balcony

# =============================================================================
# SCRAPING BEHAVIOR
# =============================================================================

MAX_LISTINGS_TO_SCRAPE = 10        # Total listings to scrape from search results
TARGET_SHORTLIST = 2               # Target number of properties after filtering
PAGE_LOAD_TIMEOUT = 30000           # Page load timeout in milliseconds
DETAIL_PAGE_TIMEOUT = 45000         # Timeout for property detail page elements
MIN_DELAY = 2                       # Minimum seconds between page navigations
MAX_DELAY = 5                       # Maximum seconds between page navigations

# =============================================================================
# BROWSER SETTINGS
# =============================================================================

VIEWPORT_WIDTH = 1366
VIEWPORT_HEIGHT = 768
HEADED = True                        # Run browser in headless mode
RECORD_VIDEO = False     # If True, records the browser session to mp4
VIDEO_DIR = "output"

# =============================================================================
# AGENT INSPECTION / DEBUG SETTINGS
# =============================================================================

MAX_DEBUG_RUNS = 5                  # Keep last N debug runs in debug/history/
DEBUG_DIR = "debug"                 # Root debug artifacts directory

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)

# =============================================================================
# MAGICBRICKS URLs
# =============================================================================

MAGICBRICKS_URL = "https://www.magicbricks.com"

# =============================================================================
# LLM SETTINGS
# =============================================================================

LLM_MODEL = "gemini-3.1-flash-lite"   # Used for ranking and recommendations

# Scoring weights for LLM ranking (must sum to 1.0)
SCORING_WEIGHTS = {
    "rent_value": 0.30,         # Rent value for money (rent vs area, furnishing)
    "floor_preference": 0.25,   # Higher floors preferred, 12+ required
    "property_age": 0.20,       # Newer = better, <= 5 years required
    "location_quality": 0.15,   # Closer to Whitefield center = better
    "amenities": 0.10,          # Balcony quality, gym, parking, etc.
}

# =============================================================================
# OUTPUT SETTINGS
# =============================================================================

OUTPUT_DIR = "output"
RESULTS_JSON = "output/results.json"
REPORT_MD = "output/report.md"
REPORT_HTML = "output/min_5_report.html"
