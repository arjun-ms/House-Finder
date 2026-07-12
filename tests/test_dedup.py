"""Tests for deduplication of scraped properties across overlapping location searches."""
import sys
sys.path.insert(0, ".")


def test_deduplicate_by_url_removes_exact_duplicates():
    """When the same listing_url appears from two location searches, keep only the first."""
    from agents.browser_agent import deduplicate_properties

    props = [
        {"property_name": "Desai Radiant", "listing_url": "https://magicbricks.com/desai-radiant-pdpid-123", "price": 10800000},
        {"property_name": "United Dreamcity", "listing_url": "https://magicbricks.com/united-pdpid-456", "price": 11000000},
        {"property_name": "Desai Radiant", "listing_url": "https://magicbricks.com/desai-radiant-pdpid-123", "price": 10800000},  # duplicate
        {"property_name": "Subhodaya Laurus", "listing_url": "https://magicbricks.com/subhodaya-pdpid-789", "price": 20600000},
        {"property_name": "United Dreamcity", "listing_url": "https://magicbricks.com/united-pdpid-456", "price": 11000000},  # duplicate
    ]

    result = deduplicate_properties(props)

    assert len(result) == 3, f"Expected 3, got {len(result)}"
    assert result[0]["property_name"] == "Desai Radiant"
    assert result[1]["property_name"] == "United Dreamcity"
    assert result[2]["property_name"] == "Subhodaya Laurus"


def test_deduplicate_preserves_order():
    """Deduplication preserves insertion order (first occurrence wins)."""
    from agents.browser_agent import deduplicate_properties

    props = [
        {"property_name": "B", "listing_url": "url-b"},
        {"property_name": "A", "listing_url": "url-a"},
        {"property_name": "B-copy", "listing_url": "url-b"},  # same URL, different name
    ]

    result = deduplicate_properties(props)

    assert len(result) == 2
    assert result[0]["property_name"] == "B"  # first occurrence wins
    assert result[1]["property_name"] == "A"


def test_deduplicate_empty_list():
    """Deduplication of an empty list returns empty list."""
    from agents.browser_agent import deduplicate_properties
    assert deduplicate_properties([]) == []


if __name__ == "__main__":
    test_deduplicate_by_url_removes_exact_duplicates()
    print("PASS: test_deduplicate_by_url_removes_exact_duplicates")
    test_deduplicate_preserves_order()
    print("PASS: test_deduplicate_preserves_order")
    test_deduplicate_empty_list()
    print("PASS: test_deduplicate_empty_list")
    print("\nAll dedup tests passed!")
