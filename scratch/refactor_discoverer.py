import re

with open('keyword_discoverer.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Refactor discover_watch_keywords signature and pass args to discover_keywords_from_bestsellers
code = re.sub(
    r'def discover_watch_keywords\(limit: int = 10\) -> list\[str\]:',
    r'def discover_watch_keywords(limit: int = 10, site_id: str = None, amazon_url: str = None, niche_prompt: str = None) -> list[str]:',
    code
)

code = re.sub(
    r'keywords = discover_keywords_from_bestsellers\(limit=limit\)',
    r'keywords = discover_keywords_from_bestsellers(limit=limit, custom_url=amazon_url)',
    code
)

code = re.sub(
    r'keywords = generate_seed_queries\(\)\[:limit\]',
    r'keywords = generate_seed_queries(niche_prompt)[:limit]',
    code
)

code = re.sub(
    r'result = database\.add_keywords_to_pool\(\[kw\]\)',
    r'result = database.add_keywords_to_pool([kw], site_id=site_id)',
    code
)

# Refactor discover_keywords_from_bestsellers
code = re.sub(
    r'def discover_keywords_from_bestsellers\(limit: int = 10\) -> list\[str\]:',
    r'def discover_keywords_from_bestsellers(limit: int = 10, custom_url: str = None) -> list[str]:',
    code
)

code = re.sub(
    r'for url in BESTSELLER_URLS:',
    r'urls_to_scrape = [custom_url] if custom_url else BESTSELLER_URLS\n    for url in urls_to_scrape:',
    code
)

# Refactor generate_seed_queries
code = re.sub(
    r'def generate_seed_queries\(\) -> list\[str\]:',
    r'def generate_seed_queries(niche_prompt: str = None) -> list[str]:',
    code
)

code = re.sub(
    r'brands  = \["SKMEI", "CURREN", "CASIO", "TIMEX", "Garmin", "Fossil", "Seiko"\]\n    intents = \["best budget", "review", "waterproof", "cheap", "tactical", "top rated"\]\n\n    queries = \[\]\n    for brand in brands:\n        for intent in intents:\n            queries\.append\(f"\{intent\} \{brand\} watch"\)',
    r'''if niche_prompt:
        brands = [niche_prompt.split(" ")[0]] # Simple fallback if prompt provided
        item_type = "product"
        if "watch" in niche_prompt.lower(): item_type = "watch"
        elif "laptop" in niche_prompt.lower(): item_type = "laptop"
    else:
        brands  = ["SKMEI", "CURREN", "CASIO", "TIMEX", "Garmin", "Fossil", "Seiko"]
        item_type = "watch"

    intents = ["best budget", "review", "waterproof", "cheap", "top rated"]
    queries = []
    for brand in brands:
        for intent in intents:
            queries.append(f"{intent} {brand} {item_type}")''',
    code
)

with open('keyword_discoverer.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("keyword_discoverer.py refactored.")
