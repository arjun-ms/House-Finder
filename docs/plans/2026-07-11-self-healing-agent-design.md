# Self-Healing Agent Architecture Design

## Overview
To maximize scraping speed and accuracy while maintaining resilience against website UI/DOM changes (e.g., MagicBricks redesigning their layout), we are implementing a "Self-Healing Agent" (Fast Path / Slow Path) architecture. This approach utilizes lightning-fast deterministic Playwright scripts for standard execution and falls back to a Vision LLM agent only when the primary execution fails.

## Architecture & Data Flow
We will wrap core Playwright actions (e.g., `page.click('.mb-search__btn')`) inside a Python decorator: `@self_healing_action("Click the search button")`.

**The Data Flow:**
1. **The Fast Path:** The raw Playwright script executes hardcoded logic.
2. **The Interception:** If a DOM change occurs and Playwright throws a `TimeoutError`, the decorator intercepts the exception instead of crashing the pipeline.
3. **The Slow Path:** The decorator pauses execution and passes the live `BrowserContext` to a `browser-use` LLM Agent, alongside the intent (e.g., "The fast script failed to 'Click the search button'. Find it and click it").
4. **The Handoff:** The LLM uses vision and DOM tools to find the redesigned button, executes the click, and terminates. Control is returned seamlessly to the fast Playwright script.

## Components & Error Handling

### Core Components
1. **`SelfHealingAgent` Component:** A subclass or configuration of the LLM agent that strictly attaches to an already open Playwright `Page`, ensuring the agent shares active cookies, sessions, and the exact DOM state without refreshing.
2. **`FallbackPromptBuilder` Component:** Generates context for the LLM. It captures a screenshot of the broken state, grabs the URL, and compiles the system prompt containing the failed intent.

### Failsafes and Error Handling
- **Step Limits:** The LLM agent is strictly bounded to `max_steps=3` to prevent endless hallucination loops.
- **Fatal Fallback:** If the LLM exceeds its step limit or encounters an unrecoverable error, the decorator throws a fatal `SiteRedesignException`. The main pipeline catches this, safely closes the browser, and logs a critical alert indicating a human developer must intervene.

## Testing Strategy
1. **Unit Testing the Decorator:** Isolated Python tests that manually raise `playwright.TimeoutError` inside dummy functions wrapped with `@self_healing_action`. This verifies that the routing logic correctly boots the fallback agent and handles fatal exceptions cleanly.
2. **Chaos Engineering (Integration Testing):** Running the fast path against a local mock of the target search page, utilizing a background Javascript timer to intentionally rename CSS classes (e.g., `.mb-search__btn` to `.new-btn-layout`) right before the script attempts to click it. This verifies the agent can automatically catch the failure, analyze the modified DOM, and successfully click the renamed element.
