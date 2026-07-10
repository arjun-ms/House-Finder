"""
Agent inspection and diagnosis tools for the browser agent.

Provides 4 structured tools that give the agent observability
into the page state at every step, without requiring LLM calls:

1. take_debug_screenshot(step_name) - Visual snapshot of the page
2. dump_dom_around(selector, step_name) - Raw HTML of a DOM region
3. find_clickable_by_text(text) - Search visible page for clickable elements
4. wait_and_retry(action, retries, step_name) - Retry with inspection on failure
"""

import asyncio
import shutil
from datetime import datetime
from pathlib import Path
from playwright.async_api import Page

import config


class AgentTools:
    """Inspection toolkit attached to a Playwright page."""

    def __init__(self, page: Page):
        self.page = page
        self.run_id = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self._step_counter = 0

        # Directory paths
        self._debug_dir = Path(config.DEBUG_DIR)
        self._latest_dir = self._debug_dir / "latest"
        self._history_dir = self._debug_dir / "history"
        self._run_dir = self._history_dir / f"run_{self.run_id}"

        self._setup_dirs()

    # -------------------------------------------------------------------------
    # Directory management
    # -------------------------------------------------------------------------

    def _setup_dirs(self):
        """Create debug directories and clean up old runs."""
        self._run_dir.mkdir(parents=True, exist_ok=True)

        # Recreate latest/ as empty
        if self._latest_dir.exists():
            shutil.rmtree(self._latest_dir)
        self._latest_dir.mkdir(parents=True, exist_ok=True)

        self._cleanup_old_runs()
        print(f"[AGENT] Debug artifacts -> {self._latest_dir}  |  history -> {self._run_dir}")

    def _cleanup_old_runs(self):
        """Keep only the last MAX_DEBUG_RUNS history folders."""
        if not self._history_dir.exists():
            return
        runs = sorted(
            [p for p in self._history_dir.iterdir() if p.is_dir()],
            key=lambda p: p.stat().st_mtime,
        )
        max_runs = getattr(config, "MAX_DEBUG_RUNS", 5)
        while len(runs) > max_runs:
            oldest = runs.pop(0)
            shutil.rmtree(oldest)
            print(f"[AGENT] Cleaned old debug run: {oldest.name}")

    def _next_step(self, label: str) -> str:
        """Increment step counter and return a filename prefix."""
        self._step_counter += 1
        return f"step_{self._step_counter:02d}_{label}"

    def _save_to_both(self, filename: str, content: str):
        """Write a text file to both latest/ and the history run dir."""
        for directory in [self._latest_dir, self._run_dir]:
            path = directory / filename
            path.write_text(content, encoding="utf-8")

    # -------------------------------------------------------------------------
    # Tool 1: take_debug_screenshot
    # -------------------------------------------------------------------------

    async def take_debug_screenshot(self, step_name: str) -> str:
        """
        Take a screenshot of the current page state.

        Args:
            step_name: Descriptive label (e.g., "after_rent_tab", "dropdown_open")

        Returns:
            Path to the screenshot in the latest/ directory.
        """
        prefix = self._next_step(step_name)
        filename = f"{prefix}.png"

        for directory in [self._latest_dir, self._run_dir]:
            path = directory / filename
            await self.page.screenshot(path=str(path), full_page=False)

        result_path = str(self._latest_dir / filename)
        print(f"[INSPECT] Screenshot: {filename}")
        return result_path

    # -------------------------------------------------------------------------
    # Tool 2: dump_dom_around
    # -------------------------------------------------------------------------

    async def dump_dom_around(
        self, selector: str, step_name: str, max_chars: int = 5000
    ) -> str:
        """
        Dump the inner HTML of an element matching the selector.
        Falls back to the full page HTML if the selector doesn't match.

        Args:
            selector: CSS selector to target (e.g., "#serachSuggest", "body")
            step_name: Descriptive label for the output file
            max_chars: Truncate HTML to this many characters

        Returns:
            The (possibly truncated) HTML string.
        """
        prefix = self._next_step(step_name)
        filename = f"{prefix}_dom.html"

        try:
            element = self.page.locator(selector).first
            if await element.count() > 0:
                html = await element.inner_html(timeout=3000)
            else:
                html = await self.page.content()
                html = f"<!-- selector '{selector}' not found, dumping full page -->\n{html}"
        except Exception:
            html = await self.page.content()
            html = f"<!-- selector '{selector}' failed, dumping full page -->\n{html}"

        truncated = html[:max_chars]
        self._save_to_both(filename, truncated)
        print(f"[INSPECT] DOM dump: {filename} ({len(truncated)} chars)")
        return truncated

    # -------------------------------------------------------------------------
    # Tool 3: find_clickable_by_text
    # -------------------------------------------------------------------------

    async def find_clickable_by_text(
        self, text: str, tag_filter: str = None, max_results: int = 20
    ) -> list:
        """
        Search the visible page for elements containing the given text.

        Args:
            text: Text to search for (case-insensitive substring match)
            tag_filter: Optional HTML tag to restrict results (e.g., "DIV", "A")
            max_results: Maximum number of results to return

        Returns:
            List of dicts with keys: index, tag, class, text, onclick, href, visible, locator
        """
        results = []
        locator = self.page.locator(f"text=/{text}/i")
        count = await locator.count()

        for i in range(min(count, max_results * 2)):  # scan extra to account for invisible
            try:
                el = locator.nth(i)
                visible = await el.is_visible()
                if not visible:
                    continue

                tag = await el.evaluate("el => el.tagName")
                if tag_filter and tag.upper() != tag_filter.upper():
                    continue

                el_text = await el.text_content(timeout=500)
                classes = await el.evaluate("el => el.className || ''")
                onclick = await el.get_attribute("onclick") or ""
                href = await el.get_attribute("href") or ""

                results.append({
                    "index": i,
                    "tag": tag,
                    "class": classes,
                    "text": el_text.strip() if el_text else "",
                    "onclick": onclick[:150],
                    "href": href[:150],
                    "visible": visible,
                    "locator": el,
                })

                if len(results) >= max_results:
                    break
            except Exception:
                continue

        print(f"[INSPECT] find_clickable_by_text('{text}'): {len(results)} visible matches")
        for r in results[:5]:  # Print first 5 for quick visibility
            print(f"  [{r['tag']}.{r['class'][:40]}] '{r['text'][:60]}'")

        return results

    # -------------------------------------------------------------------------
    # Tool 4: wait_and_retry
    # -------------------------------------------------------------------------

    async def wait_and_retry(self, action, retries: int = 3, step_name: str = "action"):
        """
        Execute an async action with automatic retry. On failure, takes a
        screenshot and DOM dump before retrying.

        Args:
            action: An async callable (no arguments) to execute
            retries: Number of attempts before giving up
            step_name: Label for debug artifacts

        Returns:
            The return value of the action on success.

        Raises:
            The last exception if all retries fail.
        """
        last_error = None
        for attempt in range(1, retries + 1):
            try:
                return await action()
            except Exception as e:
                last_error = e
                print(f"[RETRY] Attempt {attempt}/{retries} failed for '{step_name}': {e}")
                if attempt < retries:
                    await self.take_debug_screenshot(f"{step_name}_retry_{attempt}")
                    await self.dump_dom_around("body", f"{step_name}_retry_{attempt}", max_chars=8000)
                    await asyncio.sleep(1 + attempt)  # Progressive backoff

        # Final failure - capture state before raising
        await self.take_debug_screenshot(f"{step_name}_final_failure")
        await self.dump_dom_around("body", f"{step_name}_final_failure", max_chars=8000)
        raise last_error

    # -------------------------------------------------------------------------
    # Convenience: inspect a step (screenshot + DOM dump in one call)
    # -------------------------------------------------------------------------

    async def inspect_step(self, step_name: str, dom_selector: str = "body") -> dict:
        """
        Convenience method to capture both a screenshot and DOM dump for a step.

        Args:
            step_name: Label for the step (e.g., "navigate", "rent_tab")
            dom_selector: CSS selector to dump (defaults to "body")

        Returns:
            Dict with 'screenshot' path and 'dom' HTML string.
        """
        screenshot = await self.take_debug_screenshot(step_name)
        dom = await self.dump_dom_around(dom_selector, step_name)
        return {"screenshot": screenshot, "dom": dom}
