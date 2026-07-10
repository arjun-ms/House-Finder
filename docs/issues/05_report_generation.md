# Issue 5: Implement Multi-Format Report Generation

## Description
Take the raw scraped data, the filter results, and the LLM's ranked output, and format them into readable reports (`report_generator.py`).

## Requirements
- Generate `results.json`: A complete, machine-readable dataset including all scraped properties, filter statuses, and raw LLM rankings.
- Generate `report.md`: A clean Markdown file summarizing the top 3 picks and the LLM's reasoning.
- Generate `report.html`: A styled, visual HTML report suitable for viewing in a web browser.
- Ensure all outputs are saved securely into the `output/` directory.

## Acceptance Criteria
- Running the full pipeline results in the creation of `results.json`, `report.md`, and `report.html` in the output folder.
- The HTML report renders correctly in a standard browser.
- The JSON file is valid and well-structured.
