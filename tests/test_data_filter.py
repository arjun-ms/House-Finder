import pytest
import config
from data_filter import filter_properties

# Ensure config matches our strict requirements for the test
config.MIN_FLOOR = 12
config.MAX_PROPERTY_AGE = 5
config.REQUIRE_BALCONY = True
config.TARGET_SHORTLIST = 0  # Set to 0 so it DOES NOT relax filters for a small test list

def test_floor_filter():
    properties = [
        {"property_name": "Floor 15", "floor_number": 15, "property_age": 2, "balcony_count": 1},
        {"property_name": "Floor 12", "floor_number": 12, "property_age": 2, "balcony_count": 1},
        {"property_name": "Floor 11", "floor_number": 11, "property_age": 2, "balcony_count": 1},
        {"property_name": "Floor 5", "floor_number": "5 out of 10", "property_age": 2, "balcony_count": 1},
    ]
    
    filtered, excluded = filter_properties(properties)
    
    # Floor 15 and 12 should pass
    assert len(filtered) == 2
    assert any(p["property_name"] == "Floor 15" for p in filtered)
    assert any(p["property_name"] == "Floor 12" for p in filtered)
    
    # Floor 11 and 5 should be excluded
    assert len(excluded) == 2
    assert any(p["property_name"] == "Floor 11" for p in excluded)
    assert any(p["property_name"] == "Floor 5" for p in excluded)


def test_age_filter():
    properties = [
        {"property_name": "Brand New", "floor_number": 15, "property_age": 0, "balcony_count": 1},
        {"property_name": "5 Years", "floor_number": 15, "property_age": 5, "balcony_count": 1},
        {"property_name": "6 Years", "floor_number": 15, "property_age": 6, "balcony_count": 1},
        {"property_name": "10 Years String", "floor_number": 15, "property_age": "10 Years", "balcony_count": 1},
    ]
    
    filtered, excluded = filter_properties(properties)
    
    # 0 and 5 years should pass
    assert len(filtered) == 2
    assert any(p["property_name"] == "Brand New" for p in filtered)
    assert any(p["property_name"] == "5 Years" for p in filtered)
    
    # 6 and 10 years should be excluded
    assert len(excluded) == 2
    assert any(p["property_name"] == "6 Years" for p in excluded)
    assert any(p["property_name"] == "10 Years String" for p in excluded)


def test_balcony_filter():
    properties = [
        {"property_name": "Has 2 Balconies", "floor_number": 15, "property_age": 2, "balcony_count": 2},
        {"property_name": "Has 1 Balcony", "floor_number": 15, "property_age": 2, "balcony_count": "1"},
        {"property_name": "Balcony Yes", "floor_number": 15, "property_age": 2, "balcony_count": "Yes"},
        {"property_name": "No Balcony", "floor_number": 15, "property_age": 2, "balcony_count": 0},
    ]
    
    filtered, excluded = filter_properties(properties)
    
    # 2, 1, and "Yes" should pass
    assert len(filtered) == 3
    assert any(p["property_name"] == "Has 2 Balconies" for p in filtered)
    assert any(p["property_name"] == "Has 1 Balcony" for p in filtered)
    assert any(p["property_name"] == "Balcony Yes" for p in filtered)
    
    # 0 should be excluded
    assert len(excluded) == 1
    assert excluded[0]["property_name"] == "No Balcony"


def test_perfect_match_vs_all_failures():
    properties = [
        # Perfect
        {"property_name": "Perfect Match", "floor_number": 12, "property_age": 5, "balcony_count": 1},
        # Fails all
        {"property_name": "Fails All", "floor_number": 1, "property_age": 15, "balcony_count": 0},
    ]
    
    filtered, excluded = filter_properties(properties)
    
    assert len(filtered) == 1
    assert filtered[0]["property_name"] == "Perfect Match"
    
    assert len(excluded) == 1
    assert excluded[0]["property_name"] == "Fails All"
    assert len(excluded[0]["exclusion_reason"]) == 3 # Should have 3 reasons for exclusion
