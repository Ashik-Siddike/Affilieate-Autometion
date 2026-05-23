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

# ── Fallback Seed Keywords ──
DEFAULT_SEED_QUERIES = [
    "best tactical watch",
    "best budget watch",
    "waterproof watch",
    "military watch",
    "digital watch",
    "best watch under 50",
    "outdoor watch",
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


def _filter_niche_keywords(keywords: list[str], niche_prompt: str) -> list[str]:
    """
    শুধুমাত্র নির্দিষ্ট niche-এর keywords ফিল্টার করে।
    """
    if niche_prompt:
        # Extract the main noun/subject from niche prompt (e.g. "gaming laptop" -> "laptop")
        niche_words = set(niche_prompt.lower().split())
        main_word = niche_prompt.lower().split()[-1] if len(niche_prompt.split()) > 0 else "product"
    else:
        main_word = "watch"
        niche_words = {"watch", "watches", "timepiece", "chronograph", "wristwatch", "tactical", "budget"}

    EXCLUDE_WORDS = {
        "apple watch", "samsung watch", "galaxy watch",  # Premium brands
        "rolex", "omega", "breitling", "tag heuer", "free", "download", "crack", "torrent"
    }

    filtered = []
    for kw in keywords:
        kw_lower = kw.lower().strip()

        if any(ex in kw_lower for ex in EXCLUDE_WORDS):
            continue

        # Must contain the main niche word or intent
        if main_word in kw_lower or any(niche in kw_lower for niche in niche_words):
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


def discover_trending_keywords(limit: int = 15, niche_prompt: str = None) -> list[str]:
    """
    Main entry point: Google Suggestions + Trends থেকে niche keywords discover করে।
    """
    print(f"[TRENDS] Starting Google Trends keyword discovery (target: {limit}, niche: {niche_prompt})...")
    
    all_suggestions = set()
    
    # Generate dynamic seed queries
    if niche_prompt:
        dynamic_seeds = [
            f"best {niche_prompt}",
            f"budget {niche_prompt}",
            f"top {niche_prompt}",
            f"affordable {niche_prompt}",
            f"{niche_prompt} for beginners"
        ]
        seeds = dynamic_seeds + [niche_prompt]
    else:
        seeds = list(DEFAULT_SEED_QUERIES)

    # ── Phase 1: Google Autocomplete থেকে suggestions ──
    random.shuffle(seeds)
    seeds_to_use = seeds[:10]
    
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
    base_query = f"best {niche_prompt}" if niche_prompt else random.choice(["best watch", "tactical watch", "budget watch"])
    for letter in random.sample("abcdefghijklmnopqrstuvwxyz", 5):
        suggestions = _get_google_suggestions(f"{base_query} {letter}")
        if suggestions:
            all_suggestions.update(suggestions)
        time.sleep(random.uniform(0.3, 0.8))

    print(f"[TRENDS] Total raw suggestions collected: {len(all_suggestions)}")
    
    # ── Filter & Clean ──
    filtered = _filter_niche_keywords(list(all_suggestions), niche_prompt)
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


def discover_and_save(limit: int = 15, site_id: str = None, niche_prompt: str = None) -> list[str]:
    """
    Keywords discover করে এবং Supabase keyword_pool-এ save করে।
    run_single_cycle.py থেকে call হয়।
    """
    import database
    
    keywords = discover_trending_keywords(limit=limit, niche_prompt=niche_prompt)
    
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
