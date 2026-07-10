import os
import shutil
import pytest

import config
import llm_recommender
from main import run_pipeline

@pytest.mark.asyncio
async def test_end_to_end_pipeline(monkeypatch):
    """
    End-to-end test that verifies the full pipeline runs correctly without breaking.
    It overrides configuration to scrape only 2 listings and runs the browser in headless mode.
    It also mocks the Gemini API call to prevent unnecessary API usage/costs during testing.
    """
    print("\nRunning E2E pipeline test...")
    
    # 1. Override configs for a fast, headless test
    monkeypatch.setattr(config, "MAX_LISTINGS_TO_SCRAPE", 2)
    monkeypatch.setattr(config, "HEADED", False)
    monkeypatch.setattr(config, "RECORD_VIDEO", False)
    
    test_output_dir = "test_e2e_output"
    monkeypatch.setattr(config, "OUTPUT_DIR", test_output_dir)
    monkeypatch.setattr(config, "RESULTS_JSON", os.path.join(test_output_dir, "results.json"))
    monkeypatch.setattr(config, "REPORT_MD", os.path.join(test_output_dir, "report.md"))
    monkeypatch.setattr(config, "REPORT_HTML", os.path.join(test_output_dir, "report.html"))
    
    # Clean up before test
    if os.path.exists(test_output_dir):
        shutil.rmtree(test_output_dir)
    
    # 2. Mock the Gemini API call to avoid real network requests to LLM
    def mock_rank_properties(properties):
        if not properties:
            return {"top_3": [], "best_pick": {}}
        return {
            "top_3": [
                {
                    "property_name": properties[0].get("property_name", "Test Property"),
                    "rank": 1,
                    "score": 9.5,
                    "recommendation_reason": "Mocked reason for testing.",
                    "listing_url": properties[0].get("listing_url", "")
                }
            ],
            "best_pick": {
                "property_name": properties[0].get("property_name", "Test Property"),
                "score": 9.5,
                "why": "Mocked best pick explanation."
            }
        }
    import main
    monkeypatch.setattr(main, "rank_properties", mock_rank_properties)
    
    # 3. Execute pipeline
    try:
        await run_pipeline()
        
        # 4. Verify outputs are generated
        assert os.path.exists(os.path.join(test_output_dir, "results.json")), "JSON report not found!"
        assert os.path.exists(os.path.join(test_output_dir, "report.md")), "Markdown report not found!"
        assert os.path.exists(os.path.join(test_output_dir, "report.html")), "HTML report not found!"
        
        print("\nE2E pipeline test completed successfully. Reports generated.")
        
    finally:
        # Cleanup test output directory
        if os.path.exists(test_output_dir):
            shutil.rmtree(test_output_dir)
