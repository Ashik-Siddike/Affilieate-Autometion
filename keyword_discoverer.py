"""
keyword_discoverer.py
Automatically discovers new product keywords from Amazon Best Sellers.
Saves them to the Supabase keyword_pool table for the bot to process.
"""
import re
import uuid
import requests
import database
from config import SCRAPINGANT_API_KEYS

# ── Amazon Best Seller category URLs to scrape ──
BESTSELLER_URLS = [
    # Electronics / Gadgets
    "https://www.amazon.com/Best-Sellers-Electronics/zgbs/electronics/",
    # Watches
    "https://www.amazon.com/Best-Sellers-Watches/zgbs/fashion/6358539011/",
    # Video Games / Consoles
    "https://www.amazon.com/Best-Sellers-Video-Games/zgbs/videogames/",
    # Sports & Outdoors
    "https://www.amazon.com/Best-Sellers-Sports-Outdoors/zgbs/sporting-goods/",
    # Toys & Games
    "https://www.amazon.com/Best-Sellers-Toys-Games/zgbs/toys-and-games/",
]

# ── ScrapingAnt fetch helper ──
_key_index = 0

def _fetch_with_scrapingant(url: str) -> str | None:
    """Fetches a URL via ScrapingAnt API. Rotates keys on failure."""
    global _key_index
    if not SCRAPINGANT_API_KEYS:
        print("[DISCOVER] No ScrapingAnt keys configured.")
        return None

    for _ in range(len(SCRAPINGANT_API_KEYS)):
        key = SCRAPINGANT_API_KEYS[_key_index % len(SCRAPINGANT_API_KEYS)]
        _key_index += 1
        try:
            resp = requests.get(
                "https://api.scrapingant.com/v2/general",
                params={"url": url, "x-api-key": key, "browser": "false"},
                timeout=30
            )
            if resp.status_code == 200:
                return resp.text
            print(f"[DISCOVER] ScrapingAnt returned {resp.status_code} for {url}")
        except Exception as e:
            print(f"[DISCOVER] ScrapingAnt error: {e}")
    return None


def _extract_titles_from_html(html: str) -> list[str]:
    """Extracts product titles from Amazon Best Seller HTML."""
    titles = []

    # Pattern 1: aria-label on links (most reliable)
    titles += re.findall(r'aria-label="([^"]{15,150})"', html)

    # Pattern 2: span with class _p13n-zg-list-grid-desktop
    titles += re.findall(r'class="[^"]*p13n-sc-truncate[^"]*"[^>]*>([^<]{15,150})<', html)

    # Pattern 3: plain product name divs
    titles += re.findall(r'"product-title"[^>]*>([^<]{15,150})<', html)

    # Deduplicate and clean
    seen = set()
    clean = []
    for t in titles:
        t = t.strip()
        # Skip navigation/UI text
        if len(t) < 10 or t.lower() in {"see more", "previous", "next", "best sellers"}:
            continue
        if t not in seen:
            seen.add(t)
            clean.append(t)

    return clean[:30]  # cap at 30 titles per page


def _title_to_keyword(title: str) -> str:
    """Converts a product title into a review-intent keyword."""
    # Truncate very long titles
    title = title[:80]
    # Add review intent
    return f"{title} review"


def discover_keywords_from_bestsellers(limit: int = 20) -> list[str]:
    """
    Scrapes Amazon Best Seller pages and returns a list of keyword strings.
    """
    all_keywords = []

    for url in BESTSELLER_URLS:
        if len(all_keywords) >= limit:
            break
        print(f"[DISCOVER] Scraping: {url}")
        html = _fetch_with_scrapingant(url)
        if not html:
            print(f"[DISCOVER] Failed to fetch {url} — skipping.")
            continue

        titles = _extract_titles_from_html(html)
        print(f"[DISCOVER] Found {len(titles)} titles from {url}")

        for title in titles:
            if len(all_keywords) >= limit:
                break
            kw = _title_to_keyword(title)
            all_keywords.append(kw)

    return all_keywords


def discover_watch_keywords(limit: int = 10) -> list[str]:
    """
    Main discovery entry point called by the bot (Phase 0).
    Fetches keywords and saves them to Supabase keyword_pool.
    Returns list of newly added keywords.
    """
    print(f"[DISCOVER] Starting auto keyword discovery (target: {limit} keywords)...")
    keywords = discover_keywords_from_bestsellers(limit=limit)

    if not keywords:
        print("[DISCOVER] No keywords discovered. Using seed queries as fallback.")
        keywords = generate_seed_queries()[:limit]

    added = []
    for kw in keywords:
        try:
            result = database.add_keywords_to_pool([kw])
            if result:
                added.append(kw)
                print(f"[DISCOVER] Added: {kw}")
        except Exception as e:
            # Likely a duplicate — skip silently
            if "unique" not in str(e).lower() and "23505" not in str(e):
                print(f"[DISCOVER] Warning adding '{kw}': {e}")

    print(f"[DISCOVER] Discovery complete. Added {len(added)}/{len(keywords)} keywords.")
    return added


def generate_seed_queries() -> list[str]:
    """
    Fallback: generates review-intent keywords from known brands & intents.
    Used when scraping fails.
    """
    brands  = ["SKMEI", "CURREN", "CASIO", "TIMEX", "Garmin", "Fossil", "Seiko"]
    intents = ["best budget", "review", "waterproof", "cheap", "tactical", "top rated"]

    queries = []
    for brand in brands:
        for intent in intents:
            queries.append(f"{intent} {brand} watch")
    return queries
