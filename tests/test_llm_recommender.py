import pytest
import json
from unittest.mock import patch, MagicMock
from llm_recommender import build_prompt, rank_properties

def test_build_prompt_includes_criteria():
    properties = [{"property_name": "Test Prop", "floor_number": 12, "property_age": 2}]
    prompt = build_prompt(properties)
    
    assert "Test Prop" in prompt
    assert "Rent Value for Money" in prompt
    assert "Floor Preference" in prompt

@patch("llm_recommender.get_gemini_client")
def test_rank_properties_success(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    
    # Mock the response
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "shortlisted_10": [{"rank": 1, "property_name": "Test", "listing_url": "http"}],
        "top_3": [{"rank": 1, "property_name": "Test", "listing_url": "http", "score": 9.5, "recommendation_reason": "good"}],
        "best_pick": {"property_name": "Test", "listing_url": "http", "score": 9.5, "why": "Very good"}
    })
    
    mock_client.models.generate_content.return_value = mock_response
    
    properties = [{"property_name": "Test", "floor_number": 12, "property_age": 2}]
    result = rank_properties(properties)
    
    assert "best_pick" in result
    assert result["best_pick"]["property_name"] == "Test"
    assert len(result["top_3"]) == 1

@patch("llm_recommender.get_gemini_client")
def test_rank_properties_handles_markdown_json(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    
    # Mock response wrapped in markdown
    mock_response = MagicMock()
    mock_response.text = "```json\n" + json.dumps({
        "shortlisted_10": [],
        "top_3": [],
        "best_pick": {"property_name": "Test Markdown", "listing_url": "http", "score": 9.5, "why": "Very good"}
    }) + "\n```"
    
    mock_client.models.generate_content.return_value = mock_response
    
    properties = [{"property_name": "Test"}]
    result = rank_properties(properties)
    
    assert result["best_pick"]["property_name"] == "Test Markdown"
