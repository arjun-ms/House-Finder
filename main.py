"""
House Finder - Main Pipeline Orchestrator

Entry point that runs the full property recommendation pipeline:
1. Launch browser agent
2. Search MagicBricks (form interaction)
3. Collect and scrape property listings
4. Apply Stage 2 filters
5. Send to LLM for ranking
6. Generate reports (JSON, MD, HTML)

Usage:
    python main.py
"""

import asyncio
import os
import sys
from datetime import datetime

import config
from browser_agent import run_browser_agent
from data_filter import filter_properties
from llm_recommender import rank_properties
from report_generator import generate_all_reports


def print_banner():
    """Print the startup banner."""
    print("")
    print("=" * 60)
    print("  HOUSE FINDER - Browser Agent for Property Recommendation")
    print("=" * 60)
    print("")
    print(f"  Location:     {config.SEARCH_KEYWORD}, Bangalore")
    print(f"  Type:         {config.BHK_TYPE} for {config.PROPERTY_TYPE}")
    print(f"  Budget:       Rs {config.MIN_BUDGET:,} - Rs {config.MAX_BUDGET:,}/month")
    print(f"  Floor:        {config.MIN_FLOOR}+ preferred")
    print(f"  Max Age:      {config.MAX_PROPERTY_AGE} years")
    print(f"  Balcony:      {'Required' if config.REQUIRE_BALCONY else 'Optional'}")
    print(f"  Max Listings: {config.MAX_LISTINGS_TO_SCRAPE}")
    print(f"  Browser:      {'Headed' if config.HEADED else 'Headless'}")
    print(f"  Video:        {'Recording' if config.RECORD_VIDEO else 'Disabled'}")
    print("")
    print("=" * 60)
    print("")


def print_top3_summary(llm_result: dict):
    """Print the top 3 recommendations to console."""
    print("")
    print("=" * 60)
    print("  TOP 3 PROPERTY RECOMMENDATIONS")
    print("=" * 60)
    print("")

    top_3 = llm_result.get("top_3", [])
    if not top_3:
        print("  No recommendations available.")
        return

    for prop in top_3:
        rank = prop.get("rank", "?")
        name = prop.get("property_name", "Unknown")
        score = prop.get("score", "N/A")
        reason = prop.get("recommendation_reason", "")

        try:
            print(f"  #{rank} {name}")
            print(f"     Score: {score}/10")
            print(f"     {reason}")
        except UnicodeEncodeError:
            print(f"  #{rank} {name.encode('ascii', 'replace').decode('ascii')}")
            print(f"     Score: {score}/10")
            print(f"     {reason.encode('ascii', 'replace').decode('ascii')}")
            
        if prop.get("listing_url"):
            print(f"     URL: {prop['listing_url']}")
        print("")

    # Best pick
    best = llm_result.get("best_pick", {})
    if best and best.get("property_name") != "Error":
        print("-" * 60)
        try:
            print(f"  BEST PICK: {best.get('property_name', 'N/A')}")
            print(f"  Score: {best.get('score', 'N/A')}/10")
            print("")
            print(f"  {best.get('why', 'No explanation.')}")
        except UnicodeEncodeError:
            print(f"  BEST PICK: {best.get('property_name', 'N/A').encode('ascii', 'replace').decode('ascii')}")
            print(f"  Score: {best.get('score', 'N/A')}/10")
            print("")
            print(f"  {best.get('why', 'No explanation.').encode('ascii', 'replace').decode('ascii')}")
        print("")


async def run_pipeline():
    """Execute the full pipeline."""
    start_time = datetime.now()

    # Ensure output directory exists
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)

    # =========================================================
    # STEP 1: Browser Agent - Scrape MagicBricks
    # =========================================================
    print("\n[STEP 1/4] Launching browser agent...")
    print("-" * 60)

    all_scraped = await run_browser_agent()

    if not all_scraped:
        print("\n[!] No properties were scraped. Exiting.")
        print("    Possible causes:")
        print("    - MagicBricks may have blocked the request")
        print("    - Search returned no results for the given criteria")
        print("    - Network connectivity issues")
        sys.exit(1)

    print(f"\n[STEP 1 COMPLETE] Scraped {len(all_scraped)} properties.")

    # =========================================================
    # STEP 2: Stage 2 Filtering
    # =========================================================
    print("\n[STEP 2/4] Applying Stage 2 filters...")
    print("-" * 60)

    filtered, excluded = filter_properties(all_scraped)

    if not filtered:
        print("\n[!] No properties passed Stage 2 filters.")
        print("    Consider adjusting filter criteria in config.py")
        # Still generate reports showing what was excluded
        llm_result = {
            "shortlisted_10": [],
            "top_3": [],
            "best_pick": {
                "property_name": "None",
                "why": "No properties passed all filters.",
            },
        }
    else:
        print(f"\n[STEP 2 COMPLETE] {len(filtered)} properties passed filters.")

        # =========================================================
        # STEP 3: LLM Ranking
        # =========================================================
        print("\n[STEP 3/4] Sending to Gemini for ranking...")
        print("-" * 60)

        try:
            llm_result = rank_properties(filtered)
            print(f"\n[STEP 3 COMPLETE] Ranking received.")
        except Exception as e:
            print(f"\n[!] LLM Ranking failed: {e}")
            print("    API Quota likely exhausted. Bypassing LLM and generating fallback report...")
            
            # Fallback dummy ranking so reports still generate
            dummy_top3 = []
            for i, prop in enumerate(filtered[:3], 1):
                dummy_top3.append({
                    "rank": i,
                    "property_name": prop.get("property_name", "Unknown"),
                    "score": 9.0 - (i * 0.5),
                    "recommendation_reason": "Fallback generated (LLM API quota exhausted). This property passed all Stage 2 filters.",
                    "listing_url": prop.get("listing_url")
                })
                
            llm_result = {
                "shortlisted_10": filtered[:10],
                "top_3": dummy_top3,
                "best_pick": dummy_top3[0] if dummy_top3 else {}
            }
            if llm_result["best_pick"]:
                llm_result["best_pick"]["why"] = "Fallback best pick (LLM API quota exhausted). Passed all strict criteria."

    # =========================================================
    # STEP 4: Generate Reports
    # =========================================================
    print("\n[STEP 4/4] Generating reports...")
    print("-" * 60)

    report_paths = generate_all_reports(all_scraped, filtered, excluded, llm_result)

    # =========================================================
    # SUMMARY
    # =========================================================
    elapsed = (datetime.now() - start_time).total_seconds()
    minutes = int(elapsed // 60)
    seconds = int(elapsed % 60)

    print_top3_summary(llm_result)

    print("=" * 60)
    print("  PIPELINE COMPLETE")
    print("=" * 60)
    print(f"  Time elapsed:  {minutes}m {seconds}s")
    print(f"  Scraped:       {len(all_scraped)} properties")
    print(f"  Filtered:      {len(filtered)} passed / {len(excluded)} excluded")
    print(f"  Reports:")
    print(f"    JSON:  {report_paths['json']}")
    print(f"    MD:    {report_paths['markdown']}")
    print(f"    HTML:  {report_paths['html']}")
    print("")
    print(f"  Open {report_paths['html']} in your browser to view the report.")
    print("=" * 60)
    print("")


def main():
    """Entry point."""
    print_banner()
    try:
        asyncio.run(run_pipeline())
    except KeyboardInterrupt:
        print("\n\n[!] Interrupted by user. Exiting...")
        sys.exit(0)
    except Exception as e:
        print(f"\n[!] Pipeline failed: {type(e).__name__}: {e}")
        raise


if __name__ == "__main__":
    main()
