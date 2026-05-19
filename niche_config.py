"""
niche_config.py
===============
Central registry of supported niches.
Each niche defines:
  - display_name    : Human-readable label shown in UI
  - niche_terms     : Words that identify a product as belonging to this niche
  - amazon_category : Amazon search node ID (rh=n:XXXX) for category filtering
  - default_keywords: Starter keywords added automatically when pool is empty
  - article_tags    : Tags/categories written to published articles
"""

NICHE_REGISTRY: dict[str, dict] = {
    "watches": {
        "display_name": "Watches & Timepieces",
        "niche_terms": [
            "watch", "skmei", "curren", "casio", "fossil",
            "timepiece", "wristwatch", "chronograph", "quartz",
            "digital watch", "analog watch", "smartwatch", "g-shock",
        ],
        "amazon_category": "n%3A7141123011",  # Watches & Accessories
        "amazon_sort": "review-rank",
        "default_keywords": [
            "best budget SKMEI watch",
            "best budget CURREN watch",
            "best tactical watch under 50",
            "best waterproof watch for men",
            "best military watch 2025",
        ],
        "article_tags": ["watch", "budget watch", "tactical watch", "men's accessories"],
    },

    "headphones": {
        "display_name": "Headphones & Earbuds",
        "niche_terms": [
            "headphone", "earphone", "earbuds", "earbud", "headset",
            "noise cancelling", "wireless audio", "over-ear", "in-ear",
        ],
        "amazon_category": "n%3A172541",  # Headphones
        "amazon_sort": "review-rank",
        "default_keywords": [
            "best budget wireless earbuds 2025",
            "best noise cancelling headphones under 50",
            "best earbuds for gym 2025",
            "best gaming headset under 30",
        ],
        "article_tags": ["headphones", "earbuds", "audio gear"],
    },

    "keyboards": {
        "display_name": "Mechanical Keyboards",
        "niche_terms": [
            "keyboard", "mechanical keyboard", "gaming keyboard",
            "tkl keyboard", "wireless keyboard", "keycap",
        ],
        "amazon_category": "n%3A12879431",  # Computer Keyboards
        "amazon_sort": "review-rank",
        "default_keywords": [
            "best mechanical keyboard under 50",
            "best budget gaming keyboard 2025",
            "best tkl keyboard for beginners",
        ],
        "article_tags": ["keyboard", "mechanical keyboard", "PC accessories"],
    },

    "speakers": {
        "display_name": "Portable Speakers",
        "niche_terms": [
            "speaker", "bluetooth speaker", "portable speaker",
            "wireless speaker", "soundbar", "boombox",
        ],
        "amazon_category": "n%3A1063306",  # Portable Speakers
        "amazon_sort": "review-rank",
        "default_keywords": [
            "best portable bluetooth speaker under 30",
            "best budget outdoor speaker 2025",
            "best waterproof bluetooth speaker review",
        ],
        "article_tags": ["speaker", "bluetooth speaker", "audio"],
    },

    "smart_home": {
        "display_name": "Smart Home Devices",
        "niche_terms": [
            "smart home", "smart plug", "smart bulb", "smart switch",
            "alexa", "google home", "iot", "wifi controlled",
        ],
        "amazon_category": "n%3A6563140011",  # Smart Home
        "amazon_sort": "review-rank",
        "default_keywords": [
            "best smart plug under 20 dollars",
            "best wifi smart bulb budget 2025",
            "best budget smart home devices",
        ],
        "article_tags": ["smart home", "IoT", "home automation"],
    },

    "fitness": {
        "display_name": "Fitness Equipment",
        "niche_terms": [
            "fitness", "gym", "dumbbell", "resistance band", "yoga mat",
            "pull up bar", "exercise", "workout", "jump rope",
        ],
        "amazon_category": "n%3A3407731",  # Sports & Fitness
        "amazon_sort": "review-rank",
        "default_keywords": [
            "best resistance bands under 20",
            "best home gym equipment under 50",
            "best budget dumbbells review 2025",
        ],
        "article_tags": ["fitness", "home gym", "workout gear"],
    },
}

# Default niche used when no site-specific niche is configured
DEFAULT_NICHE = "watches"


def get_niche(niche_key: str) -> dict:
    """
    Returns niche config dict for the given key.
    Falls back to DEFAULT_NICHE if key is not found.
    """
    config = NICHE_REGISTRY.get(niche_key)
    if not config:
        print(f"[NICHE] Unknown niche '{niche_key}'. Falling back to '{DEFAULT_NICHE}'.")
        config = NICHE_REGISTRY[DEFAULT_NICHE]
    return config


def get_niche_terms(niche_key: str) -> tuple:
    """Returns the niche terms tuple for keyword guard checking."""
    return tuple(get_niche(niche_key)["niche_terms"])


def get_amazon_category_param(niche_key: str) -> str:
    """Returns the URL-encoded Amazon category rh param."""
    return get_niche(niche_key)["amazon_category"]


def list_niches() -> list[tuple[str, str]]:
    """Returns list of (key, display_name) tuples for UI dropdowns."""
    return [(k, v["display_name"]) for k, v in NICHE_REGISTRY.items()]
