import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

import json
import config
from pipeline.llm_recommender import rank_properties
from pipeline.report_generator import generate_markdown_report, generate_html_report

def run_test():
    with open("output/results.json", "r") as f:
        properties = json.load(f)
        
    print(f"Loaded {len(properties)} properties from results.json")
    
    # Just take 5 valid ones to not waste tokens/time
    properties = properties[:5]
    
    # Rank
    llm_result = rank_properties(properties)
    
    # Generate report
    md_file, md_content = generate_markdown_report(llm_result, [])
    html_file = generate_html_report(md_content)
    
    print(f"Generated HTML at {html_file}")
    
if __name__ == "__main__":
    run_test()
