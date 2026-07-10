import pytest
from data_filter import filter_properties
import config

@pytest.fixture(autouse=True)
def setup_config():
    # Force strict config for tests
    config.MIN_FLOOR = 12
    config.MAX_PROPERTY_AGE = 5
    config.REQUIRE_BALCONY = True
    config.TARGET_SHORTLIST = 10  # Ensure we have enough so it doesn't trigger relaxation
    
def test_filters_out_low_floors():
    properties = [
        {"property_name": "Low Floor", "floor_number": 11, "property_age": 2, "balcony_count": 1},
        {"property_name": "High Floor", "floor_number": 12, "property_age": 2, "balcony_count": 1}
    ]
    # Set target low so relaxation doesn't happen for the low floor
    config.TARGET_SHORTLIST = 1
    
    filtered, excluded = filter_properties(properties)
    
    assert len(filtered) == 1
    assert filtered[0]["property_name"] == "High Floor"
    
    assert len(excluded) == 1
    assert excluded[0]["property_name"] == "Low Floor"
    assert "Floor 11 < 12 (excluded)" in excluded[0]["exclusion_reason"]

def test_filters_out_old_properties():
    properties = [
        {"property_name": "Old", "floor_number": 15, "property_age": 6, "balcony_count": 1},
        {"property_name": "New", "floor_number": 15, "property_age": 5, "balcony_count": 1}
    ]
    config.TARGET_SHORTLIST = 1
    
    filtered, excluded = filter_properties(properties)
    
    assert len(filtered) == 1
    assert filtered[0]["property_name"] == "New"
    
    assert len(excluded) == 1
    assert excluded[0]["property_name"] == "Old"

def test_filters_out_no_balcony():
    properties = [
        {"property_name": "No Balcony", "floor_number": 15, "property_age": 2, "balcony_count": 0},
        {"property_name": "Has Balcony", "floor_number": 15, "property_age": 2, "balcony_count": 1}
    ]
    config.TARGET_SHORTLIST = 1
    
    filtered, excluded = filter_properties(properties)
    
    assert len(filtered) == 1
    assert filtered[0]["property_name"] == "Has Balcony"
    
    assert len(excluded) == 1
    assert excluded[0]["property_name"] == "No Balcony"
    
def test_parsing_from_strings():
    properties = [
        {
            "property_name": "String Parser",
            "floor_number": "14th Floor",
            "property_age": "3 Years",
            "balcony_count": "2 Balconies"
        }
    ]
    config.TARGET_SHORTLIST = 1
    
    filtered, excluded = filter_properties(properties)
    
    assert len(filtered) == 1
    assert len(excluded) == 0
    assert filtered[0]["data_complete"] is True
