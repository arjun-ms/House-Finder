"""Test parsing data directly from SRP cards."""
import sys
sys.path.insert(0, ".")

def test_parse_srp_card():
    from agents.browser_agent import parse_srp_card_html
    
    # Mock HTML of an SRP card
    card_html = """
    <div class="mb-srp__card">
        <h2 class="mb-srp__card--title">2 BHK Apartment for Rent in Thubarahalli, Whitefield Bangalore</h2>
        <a href="https://www.magicbricks.com/bm-homes-pdpid" class="mb-srp__card__title--link"></a>
        <div class="mb-srp__card__price--amount">₹39,100</div>
        
        <div class="mb-srp__card__summary--label">Carpet Area</div>
        <div class="mb-srp__card__summary--value">1200 sqft</div>
        
        <div class="mb-srp__card__summary--label">Floor</div>
        <div class="mb-srp__card__summary--value">3 out of 10</div>
        
        <div class="mb-srp__card__summary--label">Furnishing</div>
        <div class="mb-srp__card__summary--value">Furnished</div>
        
        <div class="mb-srp__card__summary--label">Balcony</div>
        <div class="mb-srp__card__summary--value">2</div>
    </div>
    """
    
    result = parse_srp_card_html(card_html)
    
    assert result["property_name"] == "2 BHK Apartment for Rent in Thubarahalli, Whitefield Bangalore"
    assert result["price"] == 39100
    assert result["floor_number"] == 3
    assert result["total_floors"] == 10
    assert result["balcony_count"] == 2
    assert result["built_up_area"] == "1200 sqft"
    assert result["furnishing_status"] == "Furnished"
    assert result["bhk_config"] == "2 BHK"
    assert result["listing_url"] == "https://www.magicbricks.com/bm-homes-pdpid"
    
if __name__ == "__main__":
    test_parse_srp_card()
    print("PASS: test_parse_srp_card")
