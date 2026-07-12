from types import SimpleNamespace

from agents import browser_agent
import main
from agents.smart_browser_agent import _tool_param


def test_gemini_quota_failure_does_not_abort_scraping(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "AIza-test-key")

    class FakeModels:
        def generate_content(self, model, contents):
            raise Exception("429 RESOURCE_EXHAUSTED")

    class FakeClient:
        models = FakeModels()

    assert main.check_gemini_quota(client_factory=lambda api_key: FakeClient()) is False


def test_main_uses_deterministic_browser_agent():
    assert main.run_browser_agent is browser_agent.run_browser_agent


def test_browser_use_tool_params_accept_dicts_and_objects():
    assert _tool_param({"target_bhk": "2 BHK"}, "target_bhk") == "2 BHK"
    assert _tool_param(SimpleNamespace(target_bhk="2 BHK"), "target_bhk") == "2 BHK"
