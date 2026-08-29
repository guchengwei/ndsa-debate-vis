from pathlib import Path

from playwright.sync_api import sync_playwright


ARTIFACT_DIR = Path("artifacts")
ARTIFACT_DIR.mkdir(exist_ok=True)


def assert_no_page_overflow(page, label):
    overflow = page.evaluate(
        "document.documentElement.scrollWidth - document.documentElement.clientWidth"
    )
    if overflow > 2:
        raise AssertionError(f"Unexpected horizontal page overflow on {label}: {overflow}px")


with sync_playwright() as playwright:
    browser = playwright.chromium.launch()
    page_errors = []
    console_errors = []

    page = browser.new_page(viewport={"width": 1440, "height": 1100})
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
    if "Admissible:" not in detail:
        raise AssertionError(f"Expected the selected status to be explained, got: {detail!r}")

    body_text = page.locator("body").inner_text()
    expected_guidance = [
        "Red arrows run from an attacking argument to the argument it challenges.",
        "Green nodes defend the selected argument; orange nodes attack it.",
    ]
    for guidance in expected_guidance:
        if guidance not in body_text:
            raise AssertionError(f"Missing first-time guidance: {guidance!r}")
    if "Equivalent states at the same depth" in body_text:
        raise AssertionError("Internal graph-collapse wording should not be first-time UI copy")

    proof_text = page.locator("#NLP").inner_text().strip()
    if "Select a premise set" in proof_text:
        raise AssertionError("Expected the first premise set to render automatically")
    if "only supported by itself" in proof_text:
        raise AssertionError("Expected the self-premise explanation to use clearer wording")

    main_plot = page.locator("#main-graph .js-plotly-plot")
    dialogical_plot = page.locator("#dialogical .js-plotly-plot")
    if main_plot.bounding_box() is None or dialogical_plot.bounding_box() is None:
        raise AssertionError("Expected both Plotly visualizations to have rendered dimensions")

    assert_no_page_overflow(page, "desktop visualization")
    page.screenshot(path=str(ARTIFACT_DIR / "home.png"), full_page=True)

    page.goto("http://127.0.0.1:8050/use-case", wait_until="networkidle", timeout=60_000)
    page.wait_for_selector("#table", state="visible", timeout=30_000)
    source_text = page.locator("body").inner_text()
    for expected in [
        "From debate passage to proposition",
        "Source rows",
        "Read left to right",
        "Filter any column",
    ]:
        if expected not in source_text:
            raise AssertionError(f"Missing knowledge-base guidance: {expected!r}")

    headers = page.locator("#table th").all_inner_texts()
    header_text = " ".join(headers)
    expected_order = ["number", "speaker", "type", "proof", "proposition", "origin", "group"]
    positions = [header_text.find(column) for column in expected_order]
    if any(position < 0 for position in positions) or positions != sorted(positions):
        raise AssertionError(f"Unexpected knowledge-base column order: {headers!r}")

    assert_no_page_overflow(page, "desktop knowledge base")
    page.screenshot(path=str(ARTIFACT_DIR / "knowledge-base.png"), full_page=True)

    mobile = browser.new_page(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
    mobile.on("pageerror", lambda error: page_errors.append(f"mobile: {error}"))
    mobile.on(
        "console",
        lambda message: console_errors.append(f"mobile: {message.text}")
        if message.type == "error"
        else None,
    )

    mobile.goto("http://127.0.0.1:8050", wait_until="networkidle", timeout=60_000)
    mobile.wait_for_selector("#main-graph .js-plotly-plot", timeout=30_000)
    mobile.wait_for_selector("#dialogical .js-plotly-plot", timeout=30_000)
    assert_no_page_overflow(mobile, "mobile visualization")
    mobile.screenshot(path=str(ARTIFACT_DIR / "mobile-home.png"), full_page=True)

    mobile.goto("http://127.0.0.1:8050/use-case", wait_until="networkidle", timeout=60_000)
    mobile.wait_for_selector("#table", state="visible", timeout=30_000)
    assert_no_page_overflow(mobile, "mobile knowledge base")
    mobile.screenshot(path=str(ARTIFACT_DIR / "mobile-knowledge-base.png"), full_page=True)

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
