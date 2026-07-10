# Issue 1: Setup Browser Automation for MagicBricks

## Description
Implement the core browser automation component (`browser_agent.py`) using Playwright. This module is responsible for launching a headed browser, navigating to MagicBricks, and recording the session for debugging purposes.

## Requirements
- Launch a Chromium browser in headed mode (visible).
- Navigate to `https://www.magicbricks.com`.
- Apply a custom user agent to mimic a real Chrome browser on Windows.
- Enable video recording of the browser session and save it to the `output/` directory.
- Incorporate random delays (2-5 seconds) between navigations to mimic human behavior.
- Set a page load timeout of 30 seconds.

## Acceptance Criteria
- Playwright script successfully opens MagicBricks in headed mode.
- A `.webm` video is recorded and saved to the `output/` directory after execution.
- No immediate bot-blocks occur upon initial load.
