import pytest
import os
import json
from report_generator import generate_all_reports

@pytest.fixture
def sample_data():
    return (
        [{"property_name": "Prop 1"}],  # scraped
        [{"property_name": "Prop 1", "data_complete": True}],  # filtered
        [{"property_name": "Prop 2 excluded"}],  # excluded
        {
            "shortlisted_10": [{"property_name": "Prop 1"}],
            "top_3": [{"property_name": "Prop 1", "recommendation_reason": "good"}],
            "best_pick": {"property_name": "Prop 1", "why": "very good"}
        }  # ranking
    )

def test_generate_reports(sample_data, monkeypatch):
    import config
    import tempfile
    from pathlib import Path
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        # Override config paths to write to tmp_path
        monkeypatch.setattr(config, "OUTPUT_DIR", str(tmp_path))
        monkeypatch.setattr(config, "RESULTS_JSON", str(tmp_path / "results.json"))
        monkeypatch.setattr(config, "REPORT_MD", str(tmp_path / "report.md"))
        monkeypatch.setattr(config, "REPORT_HTML", str(tmp_path / "report.html"))
        
        scraped, filtered, excluded, ranking = sample_data
        generate_all_reports(scraped, filtered, excluded, ranking)
        
        # Check JSON
        assert (tmp_path / "results.json").exists()
        with open(tmp_path / "results.json", "r") as f:
            data = json.load(f)
            assert data["stats"]["total_scraped"] == 1
            
        # Check Markdown
        assert (tmp_path / "report.md").exists()
        with open(tmp_path / "report.md", "r", encoding="utf-8") as f:
            md_content = f.read()
            assert "Prop 1" in md_content
            
        # Check HTML
        assert (tmp_path / "report.html").exists()
        with open(tmp_path / "report.html", "r", encoding="utf-8") as f:
            html_content = f.read()
            assert "<html" in html_content
            assert "Prop 1" in html_content
