from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.parse import urlsplit
from uuid import uuid4

from axe_playwright_python.sync_playwright import Axe
from playwright.sync_api import sync_playwright

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
URL = os.environ.get("PEWS_QA_URL", "http://127.0.0.1:18439/")
URL_PARTS = urlsplit(URL)
EXPECTED_ORIGIN = f"{URL_PARTS.scheme}://{URL_PARTS.netloc}"
CAPTURE_SANITIZED = os.environ.get("PEWS_CAPTURE_SANITIZED") == "1"
if CAPTURE_SANITIZED and URL != "http://127.0.0.1:18440/":
    raise RuntimeError("Screenshots are allowed only against the sanitized fixture on port 18440")
ARTIFACTS = Path(__file__).resolve().parents[1] / "artifacts" / "sanitized-browser"


def run_viewport(browser, name, width, height, mutate=False):
    page = browser.new_page(viewport={"width": width, "height": height})
    console_errors = []
    unexpected_network = []
    page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
    page.on(
        "request",
        lambda request: unexpected_network.append(request.url)
        if not request.url.startswith(f"{EXPECTED_ORIGIN}/")
        else None,
    )
    page.goto(URL, wait_until="networkidle")
    page.get_by_role("heading", name="What needs attention?").wait_for()
    state = page.locator(".source-health small").inner_text()
    plan_count = page.locator(".plan-row").count()
    geometry = page.evaluate("""() => ({innerWidth, clientWidth: document.documentElement.clientWidth, scrollWidth: document.documentElement.scrollWidth})""")
    if mutate:
        action_title = f"Browser QA transient {uuid4().hex[:8]}"
        page.get_by_role("button", name="Add follow-up").click()
        page.get_by_label("What needs to happen?").fill(action_title)
        page.get_by_label("Owner").fill("QA owner")
        page.get_by_role("button", name="Add follow-up", exact=True).last.click()
        page.wait_for_load_state("networkidle")
        action = page.locator(".action-card").filter(has_text=action_title)
        action.wait_for()
        action.get_by_role("button", name="Mark complete").click()
        action.wait_for(state="detached")
    browser_storage = page.evaluate(
        """async () => ({local: localStorage.length, session: sessionStorage.length, indexed: (await indexedDB.databases()).length})"""
    )
    axe_results = Axe().run(page).response["violations"]
    if CAPTURE_SANITIZED:
        ARTIFACTS.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(ARTIFACTS / f"{name}.png"), full_page=True)
    result = {
        "viewport": name,
        "width": width,
        "height": height,
        "source_state": state,
        "plan_count": plan_count,
        "geometry": geometry,
        "console_error_count": len(console_errors),
        "console_errors": [message[:240] for message in console_errors],
        "unexpected_network_count": len(unexpected_network),
        "browser_storage": browser_storage,
        "axe_violation_count": len(axe_results),
        "axe_violations": [{"id": item["id"], "impact": item.get("impact")} for item in axe_results],
        "local_action_created": mutate,
    }
    page.close()
    return result


with sync_playwright() as playwright:
    browser = playwright.chromium.launch(executable_path=CHROME, headless=True)
    results = [
        run_viewport(browser, "desktop-1440", 1440, 1000, mutate=True),
        run_viewport(browser, "mobile-390", 390, 844),
    ]
    browser.close()

for result in results:
    assert result["source_state"].lower().startswith("fresh"), result
    assert result["plan_count"] > 0, result
    assert result["geometry"]["scrollWidth"] <= result["geometry"]["clientWidth"], result
    assert result["console_error_count"] == 0, result
    assert result["unexpected_network_count"] == 0, result
    assert result["browser_storage"] == {"local": 0, "session": 0, "indexed": 0}, result
    assert result["axe_violation_count"] == 0, result
print(json.dumps(results, indent=2))
