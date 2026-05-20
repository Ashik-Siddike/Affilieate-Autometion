"""
google_trends_discoverer.py
Google Trends থেকে trending watch/gadget keywords discover করে।
Suggestions API ব্যবহার করে — কোনো API key লাগে না।
"""
import requests
import json
import re
import time
import random

# ── Watch/Gadget Niche-এর জন্য Seed Keywords ──
SEED_QUERIES = [
    "best tactical watch",
    "best budget watch",
    "waterproof watch",
    "military watch",
    "SKMEI watch",
    "CURREN watch",
    "Casio watch",
    "sports watch men",
    "digital watch",
    "diving watch budget",
    "best watch under 20",
    "best watch under 50",
    "outdoor watch",
    "chronograph watch affordable",
    "fitness watch cheap",
    "survival watch",
    "field watch budget",
    "pilot watch affordable",
    "EDC watch tactical",
    "luminous watch",
]

# ── Google Trends Autocomplete API (Free, No Key Needed) ──
TRENDS_SUGGESTIONS_URL = "https://trends.google.com/trends/api/autocomplete/{keyword}"
TRENDS_RELATED_URL = "https://trends.google.com/trends/api/widgetdata/relatedsearches"
GOOGLE_SUGGEST_URL = "https://suggestqueries.google.com/complete/search"


def _get_google_suggestions(query: str) -> list[str]:
    """
    Google Autocomplete API থেকে related search suggestions নিয়ে আসে।
    এটি সবচেয়ে reliable এবং rate-limit friendly।
    """
    suggestions = []
    try:
        resp = requests.get(
            GOOGLE_SUGGEST_URL,
            params={
                "client": "firefox",  # Returns clean JSON
                "q": query,
                "hl": "en",
                "gl": "us",
            },
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            },
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            if len(data) > 1 and isinstance(data[1], list):
                suggestions = [s for s in data[1] if isinstance(s, str) and len(s) > 5]
    except Exception as e:
        print(f"[TRENDS] Google suggest error for '{query}': {e}")
    return suggestions


def _get_trends_suggestions(keyword: str) -> list[str]:
    """
    Google Trends autocomplete API থেকে trending suggestions নিয়ে আসে।
    """
    suggestions = []
    try:
        url = f"https://trends.google.com/trends/api/autocomplete/{requests.utils.quote(keyword)}"
        resp = requests.get(
            url,
            params={"hl": "en-US", "tz": "-360"},
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            },
            timeout=10,
        )
        if resp.status_code == 200:
            # Google Trends returns ")]}'\n" prefix before JSON
            text = resp.text
            if text.startswith(")]}'"):
                text = text[5:]
            data = json.loads(text)
            topics = data.get("default", {}).get("topics", [])
            for topic in topics:
                title = topic.get("title", "")
                if title and len(title) > 3:
                    suggestions.append(title)
    except Exception as e:
        print(f"[TRENDS] Trends suggest error for '{keyword}': {e}")
    return suggestions


def _filter_watch_keywords(keywords: list[str]) -> list[str]:
    """
    শুধুমাত্র watch/gadget niche-এর keywords ফিল্টার করে।
    """
    NICHE_WORDS = {
        "watch", "watches", "timepiece", "chronograph", "wristwatch",
        "skmei", "curren", "casio", "timex", "fossil", "seiko", "garmin",
        "tactical", "military", "waterproof", "dive", "digital", "analog",
        "sports", "outdoor", "budget", "cheap", "affordable", "under",
        "fitness", "smart watch", "smartwatch", "field", "pilot",
    }

    EXCLUDE_WORDS = {
        "apple watch", "samsung watch", "galaxy watch",  # Premium brands — not our niche
        "rolex", "omega", "breitling", "tag heuer",
    }

    filtered = []
    for kw in keywords:
        kw_lower = kw.lower().strip()

        # Skip excluded brands
        if any(ex in kw_lower for ex in EXCLUDE_WORDS):
            continue

        # Must contain at least one niche word
        if any(niche in kw_lower for niche in NICHE_WORDS):
            filtered.append(kw)

    return filtered


def _add_review_intent(keywords: list[str]) -> list[str]:
    """
    Keywords-এ review intent যোগ করে যদি না থাকে।
    """
    INTENT_WORDS = {"review", "best", "top", "vs", "comparison", "worth"}
    result = []
    for kw in keywords:
        kw_lower = kw.lower()
        if any(w in kw_lower for w in INTENT_WORDS):
            result.append(kw)
        else:
            result.append(f"{kw} review")
    return result


def discover_trending_keywords(limit: int = 15) -> list[str]:
    """
    Main entry point: Google Suggestions + Trends থেকে niche keywords discover করে।
    
    Returns:
        list of keyword strings ready to be saved to Supabase keyword_pool.
    """
    print(f"[TRENDS] Starting Google Trends keyword discovery (target: {limit})...")
    
    all_suggestions = set()
    
    # ── Phase 1: Google Autocomplete থেকে suggestions ──
    random.shuffle(SEED_QUERIES)  # Randomize to get varied results each run
    seeds_to_use = SEED_QUERIES[:10]  # Use 10 seeds per cycle
    
    for seed in seeds_to_use:
        suggestions = _get_google_suggestions(seed)
        if suggestions:
            print(f"[TRENDS] Google Suggest for '{seed}': {len(suggestions)} results")
            all_suggestions.update(suggestions)
        time.sleep(random.uniform(0.5, 1.5))  # Polite delay
        
        if len(all_suggestions) >= limit * 3:
            break
    
    # ── Phase 2: Google Trends Autocomplete থেকে suggestions ──
    for seed in seeds_to_use[:5]:
        trends = _get_trends_suggestions(seed)
        if trends:
            print(f"[TRENDS] Trends Suggest for '{seed}': {len(trends)} results")
            all_suggestions.update(trends)
        time.sleep(random.uniform(0.5, 1.0))

    # ── Phase 3: Alphabet modifiers (a-z) for more variety ──
    base_query = random.choice(["best watch", "tactical watch", "budget watch"])
    for letter in random.sample("abcdefghijklmnopqrstuvwxyz", 5):
        suggestions = _get_google_suggestions(f"{base_query} {letter}")
        if suggestions:
            all_suggestions.update(suggestions)
        time.sleep(random.uniform(0.3, 0.8))

    print(f"[TRENDS] Total raw suggestions collected: {len(all_suggestions)}")
    
    # ── Filter & Clean ──
    filtered = _filter_watch_keywords(list(all_suggestions))
    print(f"[TRENDS] After niche filter: {len(filtered)} keywords")
    
    # Add review intent
    with_intent = _add_review_intent(filtered)
    
    # Deduplicate and limit
    seen = set()
    final = []
    for kw in with_intent:
        kw_clean = kw.strip()
        kw_key = re.sub(r'\s+', ' ', kw_clean.lower())
        if kw_key not in seen and len(kw_clean) > 10:
            seen.add(kw_key)
            final.append(kw_clean)
    
    final = final[:limit]
    print(f"[TRENDS] Final keywords: {len(final)}")
    for i, kw in enumerate(final, 1):
        print(f"  {i}. {kw}")
    
    return final


def discover_and_save(limit: int = 15) -> list[str]:
    """
    Keywords discover করে এবং Supabase keyword_pool-এ save করে।
    run_single_cycle.py থেকে call হয়।
    """
    import database
    
    keywords = discover_trending_keywords(limit=limit)
    
    if not keywords:
        print("[TRENDS] No keywords discovered from Google Trends.")
        return []
    
    added = []
    for kw in keywords:
        try:
            result = database.add_keywords_to_pool([kw])
            if result:
                added.append(kw)
        except Exception as e:
            if "unique" not in str(e).lower() and "23505" not in str(e):
                print(f"[TRENDS] Warning adding '{kw}': {e}")
    
    print(f"[TRENDS] Saved {len(added)}/{len(keywords)} new keywords to pool.")
    return added


if __name__ == "__main__":
    # Standalone test
    keywords = discover_trending_keywords(limit=20)
    print(f"\n{'='*50}")
    print(f"Discovered {len(keywords)} keywords:")
    for i, kw in enumerate(keywords, 1):
        print(f"  {i}. {kw}")
