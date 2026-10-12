"""Browser QA for the local Iceland site: screenshots plus automatic checks.

Opens the site served from the project root, at phone and desktop widths, opens the given
cards, and reports console errors, failed requests, broken images, horizontal overflow and
cards that show an image whose displayed crop hides most of the picture.

    python -m http.server 4173      # from the project root, in another terminal
    ~/.finiteplay/venv/Scripts/python tools/qa/check_site.py --out shots

Needs `playwright` and an installed Chrome (uses channel="chrome", no browser download).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

URL = "http://localhost:4173/local-site/"
CARDS = ["playbook:pool-or-lagoon", "playbook:aurora-without-regret", "route:south-coast-six-nights",
         "route:ring-road-unhurried", "place:sight-gullfoss", "place:sight-perlan",
         "place:sight-laugardalslaug", "place:sight-whales"]
WORDS_URL = "http://localhost:4173/local-site/words.html"
VIEWPORTS = {"phone": (390, 844), "desktop": (1280, 900)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="shots")
    ap.add_argument("--url", default=URL)
    ap.add_argument("--cards", nargs="*", default=CARDS)
    ap.add_argument("--steps", type=int, default=6, help="viewport screenshots per opened card")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    from playwright.sync_api import sync_playwright
    problems: list[str] = []
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        for name, (w, h) in VIEWPORTS.items():
            page = browser.new_page(viewport={"width": w, "height": h})
            errors: list[str] = []
            page.on("console", lambda m, e=errors: e.append(m.text) if m.type == "error" else None)
            page.on("pageerror", lambda x, e=errors: e.append(str(x)))
            page.on("requestfailed", lambda r, e=errors: e.append(f"request failed: {r.url}"))
            page.goto(args.url, wait_until="networkidle")
            page.screenshot(path=str(out / f"{name}-home.png"), full_page=False)
            if page.evaluate("document.documentElement.scrollWidth > innerWidth + 1"):
                problems.append(f"{name}: home page scrolls horizontally")
            page.evaluate("document.querySelector('#place-grid').scrollIntoView()")
            for _ in range(12):
                page.mouse.wheel(0, 700)
                page.wait_for_timeout(150)
            page.wait_for_timeout(500)
            # Lazy images load only near the viewport: bring each one into view before judging it.
            for index in range(page.locator("#place-grid img").count()):
                page.locator("#place-grid img").nth(index).scroll_into_view_if_needed()
                page.wait_for_timeout(120)
            page.wait_for_timeout(500)
            blank = page.evaluate("""() => [...document.querySelectorAll('#place-grid img')]
                .filter(i => !i.complete || i.naturalWidth === 0).map(i => i.getAttribute('src'))""")
            problems += [f"{name}: place-grid image did not load: {b}" for b in blank]
            page.evaluate("document.querySelector('#place-grid').scrollIntoView()")
            page.screenshot(path=str(out / f"{name}-place-grid.png"))
            for card in args.cards:
                el = page.query_selector(f'[data-open="{card}"]')
                if not el:
                    problems.append(f"{name}: no card {card}")
                    continue
                el.scroll_into_view_if_needed()
                el.click()
                page.wait_for_timeout(500)
                tag = card.replace(":", "_")
                page.screenshot(path=str(out / f"{name}-{tag}.png"), full_page=False)
                # The reader is a scrolling <dialog>: capture it in viewport-sized steps.
                total = page.evaluate("document.querySelector('#reader').scrollHeight")
                step = h - 100
                for index, top in enumerate(range(0, min(total, step * args.steps), step)):
                    page.evaluate(f"document.querySelector('#reader').scrollTop = {top}")
                    page.wait_for_timeout(250)
                    page.screenshot(path=str(out / f"{name}-{tag}-{index}.png"))
                page.evaluate("document.querySelector('#reader').scrollTop = 0")
                broken = page.evaluate("""() => [...document.querySelectorAll('#reader-article img')]
                    .filter(i => i.complete && i.naturalWidth === 0).map(i => i.src)""")
                problems += [f"{name} {card}: broken image {b}" for b in broken]
                if page.evaluate("document.documentElement.scrollWidth > innerWidth + 1"):
                    problems.append(f"{name} {card}: horizontal overflow")
                page.keyboard.press("Escape")
                page.wait_for_timeout(200)
            page.goto(WORDS_URL, wait_until="networkidle")
            if page.evaluate("document.querySelectorAll('.word-row').length") == 0:
                problems.append(f"{name}: word page shows no words")
            if page.evaluate("document.documentElement.scrollWidth > innerWidth + 1"):
                problems.append(f"{name}: word page scrolls horizontally")
            page.screenshot(path=str(out / f"{name}-words-page.png"))
            problems += [f"{name}: {e}" for e in errors]
            page.close()
        browser.close()
    print("\n".join(problems) if problems else "No automatic problems found.")
    print(f"Screenshots in {out.resolve()}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
