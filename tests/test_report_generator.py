import pytest
import os
import json
from pipeline.report_generator import generate_json_report, generate_markdown_report, generate_html_report, generate_all_reports
import config

@pytest.fixture
def sample_data():
    all_scraped = [{"name": "A"}, {"name": "B"}]
    filtered = [{"name": "A"}]
    excluded = [{"name": "B", "exclusion_reason": ["Too old"]}]
    llm_result = {
        "shortlisted_10": [{"rank": 1, "property_name": "A"}],
        "top_3": [{"rank": 1, "property_name": "A", "recommendation_reason": "Good"}],
        "best_pick": {"property_name": "A", "score": 9, "why": "Best value"}
    }
    return all_scraped, filtered, excluded, llm_result

import tempfile
import shutil

@pytest.fixture
def local_tmp_path():
    temp_dir = os.path.join(os.getcwd(), "test_tmp")
    os.makedirs(temp_dir, exist_ok=True)
    yield temp_dir
    # Cleanup after test
    shutil.rmtree(temp_dir, ignore_errors=True)

def test_generate_json_report(local_tmp_path, sample_data):
    all_scraped, filtered, excluded, llm_result = sample_data
    
    # Override config output dir for testing
    config.OUTPUT_DIR = local_tmp_path
    config.RESULTS_JSON = os.path.join(local_tmp_path, "results.json")
    
    json_path = generate_json_report(all_scraped, filtered, excluded, llm_result)
    
    assert os.path.exists(json_path)
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    assert data["stats"]["total_scraped"] == 2
    assert data["stats"]["passed_filters"] == 1
    assert data["stats"]["excluded"] == 1
    assert data["llm_ranking"]["best_pick"]["property_name"] == "A"

def test_generate_markdown_report(local_tmp_path, sample_data):
    all_scraped, filtered, excluded, llm_result = sample_data
    
    config.OUTPUT_DIR = local_tmp_path
    config.REPORT_MD = os.path.join(local_tmp_path, "report.md")
    
    md_path, md_content = generate_markdown_report(all_scraped, filtered, excluded, llm_result)
    
    assert os.path.exists(md_path)
    assert "## Best Pick" in md_content
    assert "### A" in md_content
    assert "Best value" in md_content
    assert "Too old" in md_content

def test_generate_html_report(local_tmp_path):
    config.OUTPUT_DIR = local_tmp_path
    config.REPORT_HTML = os.path.join(local_tmp_path, "report.html")
    
    md_content = "# Title\n\nSome **bold** text."
    html_path = generate_html_report(md_content)
    
    assert os.path.exists(html_path)
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()
        
    assert "<!DOCTYPE html>" in html
    assert "<h1" in html
    assert "<strong>bold</strong>" in html
