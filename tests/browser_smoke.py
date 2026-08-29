from pathlib import Path

from playwright.sync_api import sync_playwright


ARTIFACT_DIR = Path("artifacts")
ARTIFACT_DIR.mkdir(exist_ok=True)


with sync_playwright() as playwright:
    browser = playwright.chromium.launch()
    page = browser.new_page(viewport={"width": 1440, "height": 1100})
    page_errors = []
    console_errors = []

    page.on("pageerror", lambda error: page_errors.append(str(error)))
    page.on(
        "console",
        lambda message: console_errors.append(message.text) if message.type == "error" else None,
    )

    page.goto("http://127.0.0.1:8050", wait_until="networkidle", timeout=60_000)
    page.wait_for_selector("#main-graph .js-plotly-plot", timeout=30_000)
    page.wait_for_selector("#dialogical .js-plotly-plot", timeout=30_000)
    page.wait_for_selector("#argument-detail", state="visible", timeout=30_000)
    page.wait_for_function(
        "document.querySelector('#selected-premises')?.innerText.trim().length > 0",
        timeout=30_000,
    )
    page.wait_for_function(
        "document.querySelector('#NLP')?.innerText.trim().length > 0",
        timeout=30_000,
    )

    detail = page.locator("#argument-detail").inner_text()
    if "A0" not in detail:
        raise AssertionError(f"Expected default A0 detail, got: {detail!r}")

    proof_text = page.locator("#NLP").inner_text().strip()
    if "Select a premise set" in proof_text:
        raise AssertionError("Expected the first premise set to render automatically")

    main_plot = page.locator("#main-graph .js-plotly-plot")
    dialogical_plot = page.locator("#dialogical .js-plotly-plot")
    if main_plot.bounding_box() is None or dialogical_plot.bounding_box() is None:
        raise AssertionError("Expected both Plotly visualizations to have rendered dimensions")

    page.screenshot(path=str(ARTIFACT_DIR / "home.png"), full_page=True)
    (ARTIFACT_DIR / "browser-console.txt").write_text(
        "PAGE ERRORS\n"
        + "\n".join(page_errors)
        + "\n\nCONSOLE ERRORS\n"
        + "\n".join(console_errors),
        encoding="utf-8",
    )

    browser.close()

    if page_errors:
        raise AssertionError("Browser page errors: " + " | ".join(page_errors))
    if console_errors:
        raise AssertionError("Browser console errors: " + " | ".join(console_errors))
