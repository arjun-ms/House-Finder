"""
Report Generator - Produces JSON, Markdown, and HTML outputs.

Takes the LLM ranking results and generates:
1. results.json - Complete machine-readable data
2. report.md - Clean human-readable markdown report
3. report.html - Self-contained HTML viewer for the report
"""

import json
import os
from datetime import datetime

import markdown

import config


def ensure_output_dir():
    """Create the output directory if it doesn't exist."""
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)


def generate_json_report(
    all_scraped: list[dict],
    filtered: list[dict],
    excluded: list[dict],
    llm_result: dict,
) -> str:
    """Generate the complete JSON report with full audit trail."""
    report = {
        "generated_at": datetime.now().isoformat(),
        "search_criteria": {
            "location": config.SEARCH_KEYWORD,
            "bhk": config.BHK_TYPE,
            "budget_min": config.MIN_BUDGET,
            "budget_max": config.MAX_BUDGET,
            "min_floor": config.MIN_FLOOR,
            "max_property_age": config.MAX_PROPERTY_AGE,
            "require_balcony": config.REQUIRE_BALCONY,
        },
        "stats": {
            "total_scraped": len(all_scraped),
            "passed_filters": len(filtered),
            "excluded": len(excluded),
        },
        "llm_ranking": llm_result,
        "all_scraped_properties": all_scraped,
        "filtered_properties": filtered,
        "excluded_properties": excluded,
    }

    ensure_output_dir()
    filepath = config.RESULTS_JSON
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str, ensure_ascii=False)

    print(f"[*] JSON report saved: {filepath}")
    return filepath


def generate_markdown_report(
    all_scraped: list[dict],
    filtered: list[dict],
    excluded: list[dict],
    llm_result: dict,
) -> tuple[str, str]:
    """Generate a clean markdown report."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = []
    lines.append("# House Finder - Property Recommendation Report")
    lines.append("")
    lines.append(f"*Generated: {now}*")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Search Criteria
    lines.append("## Search Criteria")
    lines.append("")
    lines.append(f"- **Location:** {config.SEARCH_KEYWORD}, Bangalore")
    lines.append(f"- **Type:** {config.BHK_TYPE} Apartment for {config.PROPERTY_TYPE}")
    lines.append(f"- **Budget:** Rs {config.MIN_BUDGET:,} - Rs {config.MAX_BUDGET:,}/month")
    lines.append(f"- **Floor:** {config.MIN_FLOOR}th floor and above")
    lines.append(f"- **Property Age:** {config.MAX_PROPERTY_AGE} years or newer")
    lines.append(f"- **Balcony:** Required")
    lines.append("")

    # Stats
    lines.append("## Scraping Summary")
    lines.append("")
    lines.append(f"- Total properties scraped: **{len(all_scraped)}**")
    lines.append(f"- Passed Stage 2 filters: **{len(filtered)}**")
    lines.append(f"- Excluded: **{len(excluded)}**")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Best Pick
    best = llm_result.get("best_pick", {})
    if best and best.get("property_name") != "Error":
        lines.append("## Best Pick")
        lines.append("")
        lines.append(f"### {best.get('property_name', 'N/A')}")
        lines.append("")
        if best.get("score"):
            lines.append(f"**Score: {best['score']}/10**")
            lines.append("")
        lines.append(best.get("why", "No reasoning provided."))
        lines.append("")
        if best.get("listing_url"):
            lines.append(f"[View on MagicBricks]({best['listing_url']})")
            lines.append("")
        lines.append("---")
        lines.append("")

    # Top 3
    top_3 = llm_result.get("top_3", [])
    if top_3:
        lines.append("## Top 3 Recommendations")
        lines.append("")
        for prop in top_3:
            rank = prop.get("rank", "?")
            name = prop.get("property_name", "Unknown")
            score = prop.get("score", "N/A")
            reason = prop.get("recommendation_reason", "No reason provided.")
            url = prop.get("listing_url", "")

            lines.append(f"### #{rank}: {name}")
            lines.append("")
            lines.append(f"**Score: {score}/10**")
            lines.append("")
            lines.append(reason)
            lines.append("")
            if url:
                lines.append(f"[View on MagicBricks]({url})")
                lines.append("")
        lines.append("---")
        lines.append("")

    # Full Shortlist Table
    shortlisted = llm_result.get("shortlisted_10", [])
    if shortlisted:
        lines.append("## All Shortlisted Properties")
        lines.append("")
        lines.append("| Rank | Property | Score | Price | Location | Floor | Age | Strengths |")
        lines.append("|------|----------|-------|-------|----------|-------|-----|-----------|")
        for prop in shortlisted:
            rank = prop.get("rank", "?")
            name = prop.get("property_name", "Unknown")
            score = prop.get("score", "N/A")
            price = prop.get("price", "N/A")
            location = prop.get("location", "N/A")
            floor = prop.get("floor_number", "N/A")
            age = prop.get("property_age", "N/A")
            strengths = ", ".join(prop.get("strengths", [])[:2])
            # Truncate long values for table
            name = name[:30] if len(str(name)) > 30 else name
            location = str(location)[:25] if len(str(location)) > 25 else location
            lines.append(f"| {rank} | {name} | {score} | {price} | {location} | {floor} | {age} | {strengths} |")
        lines.append("")
        lines.append("---")
        lines.append("")

    # Excluded Properties
    if excluded:
        lines.append("## Excluded Properties")
        lines.append("")
        lines.append("Properties that did not pass Stage 2 filters:")
        lines.append("")
        for prop in excluded[:10]:  # Show max 10
            name = prop.get("property_name") or "Unknown"
            reasons = prop.get("exclusion_reason", ["Unknown reason"])
            lines.append(f"- **{name}**: {'; '.join(reasons)}")
        if len(excluded) > 10:
            lines.append(f"- *...and {len(excluded) - 10} more*")
        lines.append("")

    md_content = "\n".join(lines)

    ensure_output_dir()
    filepath = config.REPORT_MD
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"[*] Markdown report saved: {filepath}")
    return filepath, md_content


def generate_html_report(md_content: str) -> str:
    """Generate a self-contained HTML page from markdown content."""

    # Convert markdown to HTML
    html_body = markdown.markdown(
        md_content,
        extensions=["tables", "fenced_code", "toc"],
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>House Finder - Property Recommendation Report</title>
    <style>
        :root {{
            --bg-primary: #0f1117;
            --bg-secondary: #1a1d2e;
            --bg-card: #222640;
            --text-primary: #e8eaf0;
            --text-secondary: #a0a4b8;
            --accent-primary: #6366f1;
            --accent-secondary: #818cf8;
            --accent-gold: #f59e0b;
            --accent-green: #10b981;
            --accent-red: #ef4444;
            --border-color: #2d3154;
            --shadow: 0 4px 24px rgba(0, 0, 0, 0.3);
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.7;
            padding: 0;
        }}

        .container {{
            max-width: 960px;
            margin: 0 auto;
            padding: 40px 24px;
        }}

        h1 {{
            font-size: 2.2rem;
            font-weight: 700;
            background: linear-gradient(135deg, var(--accent-secondary), var(--accent-gold));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 8px;
            letter-spacing: -0.5px;
        }}

        h2 {{
            font-size: 1.5rem;
            font-weight: 600;
            color: var(--accent-secondary);
            margin-top: 48px;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid var(--border-color);
        }}

        h3 {{
            font-size: 1.2rem;
            font-weight: 600;
            color: var(--text-primary);
            margin-top: 24px;
            margin-bottom: 12px;
        }}

        p {{
            color: var(--text-secondary);
            margin-bottom: 16px;
        }}

        em {{
            color: var(--text-secondary);
            font-style: italic;
        }}

        strong {{
            color: var(--text-primary);
            font-weight: 600;
        }}

        a {{
            color: var(--accent-secondary);
            text-decoration: none;
            transition: color 0.2s;
        }}

        a:hover {{
            color: var(--accent-gold);
            text-decoration: underline;
        }}

        hr {{
            border: none;
            border-top: 1px solid var(--border-color);
            margin: 32px 0;
        }}

        ul {{
            list-style: none;
            padding: 0;
        }}

        ul li {{
            padding: 8px 0 8px 20px;
            position: relative;
            color: var(--text-secondary);
        }}

        ul li::before {{
            content: '';
            position: absolute;
            left: 0;
            top: 16px;
            width: 8px;
            height: 8px;
            background: var(--accent-primary);
            border-radius: 50%;
        }}

        ul li strong {{
            color: var(--text-primary);
        }}

        /* Best Pick Section */
        h2 + h3 {{
            background: var(--bg-card);
            padding: 20px 24px;
            border-radius: 12px;
            border-left: 4px solid var(--accent-gold);
            margin-top: 0;
        }}

        /* Table Styling */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 16px 0 32px;
            background: var(--bg-secondary);
            border-radius: 12px;
            overflow: hidden;
            box-shadow: var(--shadow);
        }}

        thead {{
            background: var(--bg-card);
        }}

        th {{
            padding: 14px 16px;
            text-align: left;
            font-weight: 600;
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--accent-secondary);
            border-bottom: 2px solid var(--border-color);
        }}

        td {{
            padding: 12px 16px;
            font-size: 0.9rem;
            color: var(--text-secondary);
            border-bottom: 1px solid var(--border-color);
        }}

        tr:last-child td {{
            border-bottom: none;
        }}

        tr:hover td {{
            background: rgba(99, 102, 241, 0.05);
        }}

        /* Score badge */
        td:nth-child(3) {{
            font-weight: 700;
            color: var(--accent-green);
        }}

        /* Scrollable table wrapper */
        .table-wrapper {{
            overflow-x: auto;
            margin: 16px 0;
        }}

        /* Footer */
        .footer {{
            margin-top: 64px;
            padding-top: 24px;
            border-top: 1px solid var(--border-color);
            text-align: center;
            color: var(--text-secondary);
            font-size: 0.85rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        {html_body}
        <div class="footer">
            <p>Generated by House Finder Browser Agent</p>
        </div>
    </div>
</body>
</html>"""

    ensure_output_dir()
    filepath = config.REPORT_HTML
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"[*] HTML report saved: {filepath}")
    return filepath


def generate_all_reports(
    all_scraped: list[dict],
    filtered: list[dict],
    excluded: list[dict],
    llm_result: dict,
):
    """Generate all three report formats."""
    print(f"\n{'='*60}")
    print("GENERATING REPORTS")
    print(f"{'='*60}\n")

    json_path = generate_json_report(all_scraped, filtered, excluded, llm_result)
    md_path, md_content = generate_markdown_report(all_scraped, filtered, excluded, llm_result)
    html_path = generate_html_report(md_content)

    return {
        "json": json_path,
        "markdown": md_path,
        "html": html_path,
    }
