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

from dotenv import load_dotenv

load_dotenv(override=True)

import config

from agents.browser_agent import run_browser_agent as run_fast_agent
from agents.smart_browser_agent import run_browser_agent as run_smart_agent

from pipeline.data_filter import filter_properties
from pipeline.llm_recommender import rank_properties
from pipeline.report_generator import generate_all_reports


def check_gemini_quota(client_factory=None) -> bool:
    """
    Check whether Gemini is currently usable for ranking.

    Scraping does not require Gemini, so failures here should only disable the
    ranking step and should not abort the browser workflow.
    """
    print("\n[STEP 0/4] Checking Gemini API Quota...")

    key = os.environ.get("GEMINI_API_KEY", "")
    if not key:
        print("  [!] No Gemini API key found. Scraping will continue; ranking will use fallback output.")
        return False

    print(f"Gemini API key set: {key[:4]}...{key[-4:]}")

    try:
        if client_factory is None:
            from google import genai

            client_factory = lambda api_key: genai.Client(api_key=api_key)

        client = client_factory(key)
        client.models.generate_content(model=config.LLM_MODEL, contents="ping")
        print("  [+] Quota is fresh. Proceeding.\n")
        return True
    except Exception as e:
        error_str = str(e)
        if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
            print("\n" + "!" * 60)
            print("  GEMINI API RATE LIMIT HIT")
            print("!" * 60)
            print(f"\n  Quota for {config.LLM_MODEL} is exhausted.")
            print("  Scraping will continue, and ranking will use fallback output.")
            print("\n" + "!" * 60 + "\n")
        else:
            print(f"  [!] Gemini pre-flight check failed: {type(e).__name__}: {e}")
            print("  [!] Scraping will continue; ranking will use fallback output if Gemini is unavailable.")
        return False


def build_fallback_ranking(properties: list[dict], reason: str) -> dict:
    """Build a report-compatible ranking when Gemini cannot be used."""
    dummy_top3 = []
    for i, prop in enumerate(properties[:3], 1):
        dummy_top3.append({
            "rank": i,
            "property_name": prop.get("property_name", "Unknown"),
            "score": 9.0 - (i * 0.5),
            "recommendation_reason": reason,
            "listing_url": prop.get("listing_url"),
        })

    best_pick = dummy_top3[0].copy() if dummy_top3 else {}
    if best_pick:
        best_pick["why"] = reason

    return {
        "shortlisted_10": properties[:10],
        "top_3": dummy_top3,
        "best_pick": best_pick,
    }


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

    gemini_available = check_gemini_quota()

    # =========================================================
    # STEP 1: Browser Agent - Scrape MagicBricks
    # =========================================================
    print("\n[STEP 1/4] Launching browser agent...")
    print("-" * 60)

    max_retries = 1
    all_scraped = []
    
    for attempt in range(max_retries):
        try:
            print(f"[*] Attempt {attempt + 1}/{max_retries}...")

            print("[*] Attempting Fast Path (Deterministic)...")
            all_scraped = await run_fast_agent()
            
            if not all_scraped:
                print("[!] Fast Path returned 0 properties. Falling back to Smart Agent (Slow Path)...")
                all_scraped = await run_smart_agent()
                
            if all_scraped:
                break
        except Exception as e:
            error_str = str(e)
            import traceback
            traceback.print_exc()
            print(f"[!] Attempt {attempt + 1} failed: {type(e).__name__}")
            
            if "429" in error_str:
                print(f"[!] GEMINI API RATE LIMIT!")
                
                # Extract wait time if present
                import re
                wait_match = re.search(r"Please retry in ([\d\.]+)s", error_str)
                if wait_match:
                    print(f"[*] Required wait time: {float(wait_match.group(1)):.2f} seconds")
                else:
                    print(f"[*] Required wait time: Unknown (Check Google Cloud Console)")
                    
                print(f"[*] Error Details: {error_str[:300]}...")  # Print just the start to avoid massive log dumps
                
                # Comment/Uncomment this break statement for testing API limits
                break
                
            if attempt < max_retries - 1:
                print("[*] Retrying in 5 seconds...")
                await asyncio.sleep(5)
            
    if not all_scraped:
        print("\n[!] No properties were scraped after multiple attempts. Exiting.")
        print("    Possible causes:")
        print("    - MagicBricks may have blocked the request")
        print("    - Search returned no results for the given criteria")
        print("    - Network connectivity issues or flaky UI")
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
        # STEP 2.5: Deep Scrape Shortlisted Properties
        # =========================================================
        from agents.browser_agent import scrape_details_for_urls
        # from agents.smart_browser_agent import scrape_details_for_urls
        if filtered:
            detailed_props = await scrape_details_for_urls(filtered)
            if detailed_props:
                filtered = detailed_props
                # Re-apply Stage 2 filters because deep scraping may reveal hidden details (like exact price/age)
                print("\n[*] Re-applying filters on deep-scraped data...")
                filtered, new_excluded = filter_properties(filtered)
                excluded.extend(new_excluded)
                
                if not filtered:
                    print("\n[!] No properties passed filters after deep scraping.")
                    # Fallback to LLM with empty list
                    llm_result = {
                        "shortlisted_10": [],
                        "top_3": [],
                        "best_pick": {
                            "property_name": "None",
                            "why": "No properties passed after deep scraping.",
                        },
                    }
                    print("\n[STEP 3/4] Sending to Gemini for ranking...")
                    print("  Skipped: List is empty.")
                    generate_all_reports(all_scraped, filtered, excluded, llm_result)
                    return

        # =========================================================
        # STEP 3: LLM Ranking
        # =========================================================
        print("\n[STEP 3/4] Sending to Gemini for ranking...")
        print("-" * 60)

        if not gemini_available:
            print("  Skipped: Gemini is unavailable. Generating fallback ranking.")
            llm_result = build_fallback_ranking(
                filtered,
                "Fallback generated because Gemini was unavailable. This property passed the configured filters.",
            )
        else:
            try:
                llm_result = rank_properties(filtered)
                print(f"\n[STEP 3 COMPLETE] Ranking received.")
            except Exception as e:
                print(f"\n[!] LLM Ranking failed: {e}")
                print("    API quota may be exhausted. Generating fallback report...")
                llm_result = build_fallback_ranking(
                    filtered,
                    "Fallback generated because Gemini ranking failed. This property passed the configured filters.",
                )

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
