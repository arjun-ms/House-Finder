# Architecture Decision Record (ADR)
## House Finder - AI Agent Project

### 1. Hybrid AI-Deterministic Architecture
- **Context:** The AI agent (`browser-use`) struggles to paginate reliably and is expensive in terms of token usage.
- **Decision:** Use the LLM exclusively to navigate complex/ambiguous UI (such as selecting the Rent tab and handling dynamic dropdowns), then hand off execution to a deterministic Playwright parser to extract data from the Search Results Page (SRP) and Property Detail Pages (PDP).
- **Consequences:** We get the resilience of AI on dynamic elements and the speed/reliability of traditional web scraping for data extraction. 

### 2. Ambiguity Resolution Toolkit
- **Context:** The "Rent" button on MagicBricks is often hidden or shares the same text as other irrelevant links (like footer links), causing the AI agent to confidently click the wrong element.
- **Decision:** Built a custom ambiguity toolkit:
    - `safe_click_by_text(text: str)`: Raises a hard Python Exception if >1 visible element matches.
    - `inspect_clickable_elements(text: str)`: Returns only the `outerHTML` of ambiguous matches.
    - `click_element_by_css(selector: str)`: Executes the disambiguated click natively via Playwright.
- **Consequences:** The AI is strictly forced to pause, inspect the DOM snippet, and make an informed decision when ambiguity is detected, rather than guessing.

### 3. Dynamic Locality Extraction
- **Context:** Searching multiple localities in one search string on MagicBricks triggers a "sponsored listing" view that hides organic results.
- **Decision:** Iterate over localities one by one. The localities are extracted *dynamically* from the auto-suggest dropdown to ensure they exactly match what the MagicBricks backend expects (e.g., "Whitefield", "Whitefield Hoskote Road"). We use `headless=not config.HEADED` (Headed mode) for this extraction to avoid immediate bot-blocking by MagicBricks.
- **Consequences:** We cannot hardcode localities in `config.py`. The agent adapts to any `SEARCH_KEYWORD` natively.

### 4. Bypassing Free Tier LLM Quota (Vision Disabled)
- **Context:** `browser-use` sends full-page screenshots to the LLM on every navigation step by default, which instantly triggers `429 RESOURCE_EXHAUSTED` (Token Limits) on Gemini's Free Tier.
- **Decision:** We initialize the `Agent` with `use_vision=False`.
- **Consequences:** The agent relies exclusively on the accessibility/DOM tree, saving massive amounts of input tokens and allowing execution under the free tier limit.
