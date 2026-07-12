import asyncio
import os
import sys

# We MUST run this from inside src/ to ensure Python's module caching
# doesn't create duplicate instances of 'config' vs 'src.config'.
import config
from main import run_pipeline

async def run_koramangala_test():
    """Run the main pipeline but specifically for Koramangala to test standard property parsing."""
    
    # 1. Override Location natively on the exact config module main.py uses
    config.SEARCH_KEYWORD = "Koramangala, Bangalore"
    
    # 2. Override Report Output Paths
    config.REPORT_HTML = os.path.join(config.OUTPUT_DIR, "report_koramangala.html")
    config.REPORT_MD = os.path.join(config.OUTPUT_DIR, "report_koramangala.md")
    config.RESULTS_JSON = os.path.join(config.OUTPUT_DIR, "report_koramangala.json")
    
    # 3. Limit to 15 properties so the test finishes quickly
    config.MAX_LISTINGS_TO_SCRAPE = 15
    
    print("\n" + "="*60)
    print("  STARTING KORAMANGALA TEST RUN")
    print("="*60)
    print(f"[*] Target Location: {config.SEARCH_KEYWORD}")
    print(f"[*] Target Output:   {config.REPORT_HTML}")
    
    # Run the exact same pipeline used in production
    await run_pipeline()
    
if __name__ == "__main__":
    asyncio.run(run_koramangala_test())
