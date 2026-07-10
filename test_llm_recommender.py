import pytest
import json
from unittest.mock import patch, MagicMock
from llm_recommender import build_prompt, rank_properties

def test_build_prompt_contains_properties_json():
    properties = [{"property_name": "Test Prop", "rent": 50000}]
    prompt = build_prompt(properties)
    
    assert "Test Prop" in prompt
    assert "50000" in prompt
    assert "PROPERTIES DATA:" in prompt

@patch("llm_recommender.get_gemini_client")
def test_rank_properties_calls_api_and_parses_json(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    
    # Mock valid JSON response
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "shortlisted_10": [],
        "top_3": [],
        "best_pick": {"property_name": "Best", "why": "Because"}
    })
    mock_client.models.generate_content.return_value = mock_response

    properties = [{"property_name": "Prop 1"}]
    result = rank_properties(properties)
    
    # Verify API was called
    mock_client.models.generate_content.assert_called_once()
    
    # Verify result parsed
    assert result["best_pick"]["property_name"] == "Best"

@patch("llm_recommender.get_gemini_client")
def test_rank_properties_cleans_markdown_json(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    
    mock_response = MagicMock()
    raw_json = json.dumps({
        "shortlisted_10": [],
        "top_3": [],
        "best_pick": {"property_name": "Markdown", "why": "Because"}
    })
    mock_response.text = f"```json\n{raw_json}\n```"
    mock_client.models.generate_content.return_value = mock_response

    result = rank_properties([])
    assert result["best_pick"]["property_name"] == "Markdown"

@patch("llm_recommender.get_gemini_client")
def test_rank_properties_retries_and_returns_error_object(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    
    mock_response = MagicMock()
    mock_response.text = "This is not json"
    mock_client.models.generate_content.return_value = mock_response

    result = rank_properties([])
    
    # Should retry twice, so called twice
    assert mock_client.models.generate_content.call_count == 2
    
    # Should return fallback error object
    assert "error" in result
    assert result["best_pick"]["property_name"] == "Error"
