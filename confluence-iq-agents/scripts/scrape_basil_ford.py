"""Pre-scrape script for Confluence IQ Agents (Challenge 2).

Run this ONCE, ahead of the hackathon/demo, to generate static text files
of the two Basil Ford sites. The agent pipeline then reads these files —
no live scraping happens during the actual demo, per the challenge rules.

Usage:
    pip install requests beautifulsoup4 cloudscraper
    pip install playwright && python -m playwright install chromium
    python scrape_basil_ford.py

Output:
    data/site_text/basilford_com/<slug>.txt
    data/site_text/basilfordofniagarafalls_com/<slug>.txt

Each file is clean, readable page text (nav/boilerplate stripped as best-effort)
that the Market Competitor Analyst agent will read.
"""

import pathlib
import re
from datetime import datetime

HERE = pathlib.Path(__file__).resolve().parent
DATA_DIR = HERE.parent / "data" / "site_text"

# ── Site targets ──────────────────────────────────────────────────────────────
SITES = {
    "basilford_com": {
        "base_url": "https://www.basilford.com",
        "label": "Basil Ford",
        "location": "Cheektowaga, NY",
    },
    "basilfordofniagarafalls_com": {
        "base_url": "https://www.basilfordofniagarafalls.com",
        "label": "Basil Ford of Niagara Falls",
        "location": "Niagara Falls, NY",
    },
}

# ── Expected dealership page paths ────────────────────────────────────────────
# These follow the standard Dealer.com CMS structure that both sites use.
PAGE_PATHS = [
    ("home", "/"),
    ("new-inventory", "/new-inventory/index.htm"),
    ("used-inventory", "/used-inventory/index.htm"),
    ("service-center", "/service/index.htm"),
    ("parts", "/parts/index.htm"),
    ("specials-offers", "/specials/index.htm"),
    ("finance", "/finance/index.htm"),
    ("about-us", "/about/index.htm"),
    ("contact", "/contact.htm"),
]

# ── Backend: Playwright (headless Chromium) ───────────────────────────────────
# Most reliable — launches a real browser that Akamai can't distinguish from a
# human visitor. Requires `pip install playwright && python -m playwright install chromium`.
_PLAYWRIGHT_AVAILABLE = None


def _check_playwright() -> bool:
    global _PLAYWRIGHT_AVAILABLE
    if _PLAYWRIGHT_AVAILABLE is not None:
        return _PLAYWRIGHT_AVAILABLE
    try:
        import playwright  # noqa: F401

        _PLAYWRIGHT_AVAILABLE = True
        return True
    except ImportError:
        _PLAYWRIGHT_AVAILABLE = False
        return False


def _fetch_with_playwright(url: str) -> str | None:
    """Fetch *url* via headless Chromium. Bypasses Akamai bot detection."""
    if not _check_playwright():
        return None

    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return None

    import asyncio

    async def _do_fetch() -> str | None:
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                text = await page.inner_text("body")
                await browser.close()
                return text.strip()
        except Exception:
            return None

    try:
        return asyncio.run(_do_fetch())
    except Exception:
        return None


# ── Backend: cloudscraper (bypass weaker bot protections) ─────────────────────


def _fetch_with_cloudscraper(url: str) -> str | None:
    """Try cloudscraper with browser-like headers."""
    try:
        import cloudscraper
    except ImportError:
        return None

    try:
        scraper = cloudscraper.create_scraper(
            browser={
                "browser": "chrome",
                "platform": "windows",
                "mobile": False,
                "desktop": True,
            }
        )
        scraper.headers.update(
            {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-CA,en-US;q=0.9,en;q=0.8",
                "DNT": "1",
                "Upgrade-Insecure-Requests": "1",
            }
        )
        resp = scraper.get(url, timeout=20)
        if resp.status_code == 200 and len(resp.content) > 500:
            return resp.text
    except Exception:
        pass

    return None


# ── Backend: plain requests (minimal, no bypass) ──────────────────────────────


def _fetch_with_requests(url: str) -> str | None:
    """Last-resort fallback with a standard browser User-Agent."""
    try:
        import requests
    except ImportError:
        return None

    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,*/*",
            "Accept-Language": "en-CA,en-US;q=0.9",
        }
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200 and len(resp.content) > 500:
            return resp.text
    except Exception:
        pass

    return None


# ── Fetcher priority chain ────────────────────────────────────────────────────
FETCH_BACKENDS = [
    ("Playwright (headless Chromium)", _fetch_with_playwright),
    ("cloudscraper", _fetch_with_cloudscraper),
    ("requests", _fetch_with_requests),
]


def _try_fetch(url: str) -> tuple[str | None, str]:
    """Try each backend in priority order; return (html, backend_name)."""
    for name, fn in FETCH_BACKENDS:
        html = fn(url)
        if html is not None:
            return html, name
    return None, "all backends failed"


# ── Clean extraction with BeautifulSoup ───────────────────────────────────────


def _extract_text(html: str) -> str:
    """Parse HTML, return cleaned text with nav/boilerplate stripped."""
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return _simple_strip(html)

    soup = BeautifulSoup(html, "html.parser")

    # Remove non-content elements
    for selector in [
        "script",
        "style",
        "nav",
        "footer",
        "header",
        "aside",
        "noscript",
        "iframe",
        ".nav",
        ".footer",
        ".header",
        ".sidebar",
        ".menu",
        ".cookie",
        ".popup",
        ".overlay",
        '[role="navigation"]',
        '[role="banner"]',
    ]:
        for tag in soup.select(selector):
            tag.decompose()

    # Prefer <main> or <article> or <div[role=main]>
    main = (
        soup.find("main")
        or soup.find("article")
        or soup.select_one('[role="main"]')
        or soup.find("body")
    )

    if main is None:
        return _simple_strip(html)

    text = main.get_text(separator="\n", strip=True)

    # Collapse repeated blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)  # collapse inline whitespace too
    return text.strip() or _simple_strip(html)


def _simple_strip(html: str) -> str:
    """Minimal HTML-to-text when BeautifulSoup is unavailable."""
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).strip()
    sentences = [s.strip() for s in text.split(". ") if s.strip()]
    return "\n\n".join(s + "." for s in sentences)



# ── Scrape one page ───────────────────────────────────────────────────────────


def _scrape_page(_site_key: str, site: dict, slug: str, path: str) -> str | None:
    """Attempt live scrape across all backends; return *None* if all blocked."""
    url = site["base_url"].rstrip("/") + path

    html, backend = _try_fetch(url)

    if html is None:
        print(f"    {url}  BLOCKED (no backend could fetch it)")
        return None

    text = _extract_text(html)

    if len(text) < 100:
        print(f"    {url}  too short ({len(text)} chars) via {backend}")
        return None

    print(f"    {url}  OK ({len(text)} chars) via {backend}")
    return text


# ── Write a page file ─────────────────────────────────────────────────────────


def _write_page(target_dir: pathlib.Path, slug: str, content: str) -> None:
    path = target_dir / f"{slug}.txt"
    path.write_text(content.strip() + "\n", encoding="utf-8")
    print(f"      -> {path.name}")


# ── Generate fallback page when site is blocked ───────────────────────────────


# def _generate_fallback(_site_key: str, site: dict, slug: str) -> str:
 #   """Return pre-written realistic dealership page content for *slug*."""
  #  pages = FALLBACK_PAGES.get(slug, {})
   # if _site_key in pages:
    #    return pages[_site_key]

    # Generic fallback for any undiscovered page path
   # base = site["base_url"]
    #return f"""{slug.replace('-', ' ').title()} — {site['label']}

# Visit {base} for more information about this page.
# {site['label']} is a Ford dealership serving the {site['location']} area.
# Contact the dealership directly for details about {slug.replace('-', ' ')}.
#""" 


# ── Main ──────────────────────────────────────────────────────────────────────


def scrape() -> None:
    print(f"Basil Ford Pre-Scrape Tool — {datetime.now():%Y-%m-%d %H:%M}")
    print(f"Output directory: {DATA_DIR}")

    # Report available backends
    backends = []
    if _check_playwright():
        backends.append("Playwright (Chromium)")
    try:
        import cloudscraper  # noqa: F401

        backends.append("cloudscraper")
    except ImportError:
        pass
    try:
        import requests  # noqa: F401

        backends.append("requests")
    except ImportError:
        pass
    print(f"Available backends: {', '.join(backends)}\n")

    total_live = 0
    total_fallback = 0
    total_pages = len(PAGE_PATHS) * len(SITES)

    for site_key, site in SITES.items():
        target_dir = DATA_DIR / site_key
        target_dir.mkdir(parents=True, exist_ok=True)

        label = site["label"]
        print(f"\n{'='*60}")
        print(f"  {label}  ({site['location']})")
        print(f"{'='*60}")

        live_count = 0
        fallback_count = 0

        for slug, path in PAGE_PATHS:
            content = _scrape_page(site_key, site, slug, path)
            if content is None:
                print(f"    Using fallback for: {slug}")
                content = _generate_fallback(site_key, site, slug)
                fallback_count += 1
            else:
                live_count += 1

            _write_page(target_dir, slug, content)

        summary = (
            f"\n  {label}: {live_count} live, {fallback_count} fallback"
        )
        print(summary)
        total_live += live_count
        total_fallback += fallback_count

    print(f"\n{'='*60}")
    print(f"  Done — {total_live} live, {total_fallback} fallback of {total_pages} total")
    print(f"  Output: {DATA_DIR}")
    print(f"{'='*60}\n")



if __name__ == "__main__":
    scrape()
