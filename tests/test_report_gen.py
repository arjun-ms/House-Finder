import os
import sys
sys.path.insert(0, ".")

from pipeline import report_generator
import config

def test_report_generation():
    test_results = {
        "best_pick": {
            "property_name": "Premium 2BHK Whitefield",
            "score": 9.5,
            "why": "Excellent location and matches all criteria.",
            "listing_url": "https://example.com/prop1"
        },
        "top_3": [
            {
                "property_name": "Premium 2BHK Whitefield",
                "rank": 1,
                "score": 9.5,
                "recommendation_reason": "Excellent overall choice.",
                "listing_url": "https://example.com/prop1",
                "price": 35000,
                "location": "Whitefield",
                "floor_number": 14,
                "property_age": 2,
                "strengths": ["High Floor", "New Construction"]
            },
            {
                "property_name": "Sowparnika Sanvi Phase 2",
                "rank": 2,
                "score": 8.0,
                "recommendation_reason": "Good budget option.",
                "listing_url": "https://example.com/prop2",
                "price": 38000,
                "location": "Whitefield",
                "floor_number": 12,
                "property_age": 4,
                "strengths": ["Near IT Park"]
            }
        ],
        "shortlisted_10": [
            {
                "property_name": "Premium 2BHK Whitefield",
                "rank": 1,
                "score": 9.5,
                "price": 35000,
                "location": "Whitefield",
                "floor_number": 14,
                "property_age": 2,
                "strengths": ["High Floor"]
            }
        ],
        "excluded": []
    }
    
    config.REPORT_MD = "output/test_report.md"
    config.REPORT_HTML = "output/test_report.html"
    config.RESULTS_JSON = "output/test_results.json"
    
    # Generate the Markdown report
    md_file, md_content = report_generator.generate_markdown_report([], test_results["top_3"], [], test_results)
    print(f"Markdown generated at {md_file}")
    
    # Generate the HTML report
    html_file = report_generator.generate_html_report(md_content)
    print(f"HTML generated at {html_file}")
    
    with open(html_file, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    # Print the table header line from the HTML to verify the change
    for line in html_content.split('\n'):
        if "rental price(per month)" in line:
            print("FOUND IN HTML: ", line.strip())

if __name__ == "__main__":
    test_report_generation()
