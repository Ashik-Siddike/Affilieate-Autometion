import os
import uuid
import requests
import random
import json
from config import SUPABASE_URL, SUPABASE_KEY


# ---------------------------------------------------------------------------
# Supabase REST API Headers
# ---------------------------------------------------------------------------
def get_headers():
    if not SUPABASE_URL or not SUPABASE_KEY:
        return {}
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


# ---------------------------------------------------------------------------
# Connection check
# ---------------------------------------------------------------------------
def init_db():
    """Confirms connection to Supabase via REST API."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("[WARNING] Supabase credentials missing.")
        return
    try:
        url = f"{SUPABASE_URL}/rest/v1/products?select=count&limit=1"
        response = requests.get(url, headers=get_headers(), timeout=5)
        if response.status_code == 200:
            print("[OK] Connected to Supabase (REST).")
        else:
            print(f"[ERROR] Supabase connection error: {response.text}")
    except Exception as e:
        print(f"[ERROR] Supabase connection error: {e}")


# ---------------------------------------------------------------------------
# Product operations
# ---------------------------------------------------------------------------
def check_product_status(asin, site_id=None):
    """
    Checks product status.
    Returns:
        None  -> not exists
        0     -> exists but not published
        1     -> exists and published
    """
    if not SUPABASE_URL:
        return None
    try:
        url = f"{SUPABASE_URL}/rest/v1/products?asin=eq.{asin}&select=is_published" + (f"&site_id=eq.{site_id}" if site_id else "")
        response = requests.get(url, headers=get_headers(), timeout=10)
        data = response.json()
        if data and len(data) > 0:
            return 1 if data[0].get('is_published') else 0
        return None
    except Exception as e:
        print(f"DB Error (check_status): {e}")
        return None


def save_product(data_dict, site_id=None):
    """Saves a new product to the database (Upsert)."""
    if not SUPABASE_URL:
        return
    try:
        url = f"{SUPABASE_URL}/rest/v1/products"
        data = {
            "asin":         data_dict.get('asin'),
            "title":        data_dict.get('title'),
            "price":        data_dict.get('price'),
            "rating":       data_dict.get('rating'),
            "review_count": data_dict.get('review_count'),
            "image_url":    data_dict.get('image_url'),
            "product_url":  data_dict.get(\'product_url\'),
            "site_id": site_id,
        }
        headers = get_headers()
        headers["Prefer"] = "resolution=merge-duplicates"
        response = requests.post(url, headers=headers, json=data, timeout=10)
        if response.status_code >= 400:
            print(f"DB Error (save_product): {response.text}")
    except Exception as e:
        print(f"DB Error (save_product): {e}")


def mark_as_published(asin, site_id=None):
    """Marks a product as published."""
    if not SUPABASE_URL:
        return
    try:
        url = f"{SUPABASE_URL}/rest/v1/products?asin=eq.{asin}" + (f"&site_id=eq.{site_id}" if site_id else "")
        requests.patch(url, headers=get_headers(), json={'is_published': True})
    except Exception as e:
        print(f"DB Error (mark_published): {e}")


def update_post_link(asin, post_link, site_id=None):
    """Updates the post_link for a published product."""
    if not SUPABASE_URL:
        return
    try:
        url = f"{SUPABASE_URL}/rest/v1/products?asin=eq.{asin}" + (f"&site_id=eq.{site_id}" if site_id else "")
        requests.patch(url, headers=get_headers(), json={'post_link': post_link})
    except Exception as e:
        print(f"DB Error (update_link): {e}")


# ---------------------------------------------------------------------------
# Related / similar product helpers
# ---------------------------------------------------------------------------
def get_similar_products(current_asin, site_id=None, limit=2):
    """Fetches random other products for comparison tables."""
    if not SUPABASE_URL:
        return []
    try:
        url = (
            f"{SUPABASE_URL}/rest/v1/products"
            f"?asin=neq.{current_asin}"
            f"&select=title,price,rating,review_count,image_url,product_url"
            f"&limit=20" + (f"&site_id=eq.{site_id}" if site_id else "")
        )
        response = requests.get(url, headers=get_headers())
        products = response.json()
        if not products or not isinstance(products, list):
            if isinstance(products, dict):
                print(f"DB Error (similar): {products}")
            return []
        if len(products) > limit:
            return random.sample(products, limit)
        return products
    except Exception as e:
        print(f"DB Error (similar): {e}")
        return []


def get_published_posts(site_id=None, limit=5):
    """Fetches a list of recently published posts."""
    if not SUPABASE_URL:
        return []
    try:
        url = (
            f"{SUPABASE_URL}/rest/v1/products"
            f"?is_published=eq.true"
            f"&post_link=not.is.null"
            f"&select=title,post_link"
            f"&order=created_at.desc"
            f"&limit={limit}" + (f"&site_id=eq.{site_id}" if site_id else "")
        )
        response = requests.get(url, headers=get_headers())
        data = response.json()
        return [{'title': p['title'], 'link': p['post_link']} for p in data]
    except Exception as e:
        print(f"DB Error (get_posts): {e}")
        return []


def get_relevant_posts(keyword, site_id=None, limit=5):
    """
    Fetches contextually relevant posts for internal linking (Silo).
    Falls back to recent posts if no match is found.
    """
    if not SUPABASE_URL:
        return []
    try:
        clean_kw = keyword.replace(' ', '%')
        url = (
            f"{SUPABASE_URL}/rest/v1/products"
            f"?is_published=eq.true"
            f"&post_link=not.is.null"
            f"&title=ilike.*{clean_kw}*"
            f"&select=title,post_link"
            f"&order=created_at.desc"
            f"&limit={limit}" + (f"&site_id=eq.{site_id}" if site_id else "")
        )
        response = requests.get(url, headers=get_headers())
        data = response.json()

        # Fallback: mix with recent posts if no specific matches
        if not data or not isinstance(data, list):
            if isinstance(data, dict):
                print(f"DB Unknown Response: {data}")
            print("[WARNING] No direct relevant links found. Mixing with recent posts.")
            recent = get_published_posts(site_id=site_id, limit=limit)
            if not isinstance(data, list):
                data = []
            existing_links = {p.get('post_link') for p in data if isinstance(p, dict)}
            for r in recent:
                if r.get('link') not in existing_links and len(data) < limit:
                    data.append({'title': r.get('title'), 'post_link': r.get('link')})

        return [{'title': p.get('title'), 'link': p.get('post_link')} for p in data if isinstance(p, dict)]
    except Exception as e:
        print(f"DB Error (get_relevant_posts): {e}")
        return get_published_posts(site_id=site_id, limit=limit)


# ---------------------------------------------------------------------------
# Keyword pool management
# ---------------------------------------------------------------------------
def check_keyword_pool_count(site_id=None):
    """Counts how many keywords in the keyword_pool have status = 'pending'."""
    if not SUPABASE_URL:
        return 0
    try:
        headers = get_headers()
        headers["Prefer"] = "count=exact"
        count_url = f"{SUPABASE_URL}/rest/v1/keyword_pool?status=eq.pending&select=keyword" + (f"&site_id=eq.{site_id}" if site_id else "")
        resp = requests.get(count_url, headers=headers)
        if resp.status_code == 200:
            content_range = resp.headers.get("Content-Range", "")
            if "/" in content_range:
                return int(content_range.split("/")[-1])
            return len(resp.json())
        return 0
    except Exception as e:
        print(f"DB Error (check_keyword_pool): {e}")
        return 0


def get_pending_keywords_from_pool(site_id=None, limit=10):
    """Fetches pending keywords from the Supabase keyword_pool."""
    if not SUPABASE_URL:
        return []
    try:
        url = (
            f"{SUPABASE_URL}/rest/v1/keyword_pool"
            f"?status=eq.pending"
            f"&select=keyword"
            f"&limit={limit}"
        ) + (f"&site_id=eq.{site_id}" if site_id else "")
        resp = requests.get(url, headers=get_headers(), timeout=5)
        if resp.status_code == 200:
            return [row['keyword'] for row in resp.json()]
    except Exception as e:
        print(f"[ERROR] DB Error (get_pending_keywords): {e}")
    return []


def add_keywords_to_pool(keywords, site_id=None):
    """Inserts new keywords into the keyword_pool table (ignores duplicates)."""
    if not SUPABASE_URL or not keywords:
        return
    try:
        url = f"{SUPABASE_URL}/rest/v1/keyword_pool"
        headers = get_headers()
        headers["Prefer"] = "resolution=ignore-duplicates"
        payload = [{"id": str(uuid.uuid4()), "keyword": kw, "status": "pending", "site_id": site_id} for kw in keywords]
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        if response.status_code >= 400:
            print(f"DB Error (add_keywords): {response.text}")
    except Exception as e:
        print(f"DB Error (add_keywords): {e}")


def mark_keyword_completed_in_pool(keyword, site_id=None):
    """Marks a keyword as completed in the Supabase keyword_pool."""
    if not SUPABASE_URL:
        return
    try:
        url = f"{SUPABASE_URL}/rest/v1/keyword_pool?keyword=eq.{keyword}" + (f"&site_id=eq.{site_id}" if site_id else "")
        requests.patch(url, headers=get_headers(), json={"status": "completed"}, timeout=5)
    except Exception as e:
        print(f"[ERROR] DB Error (mark_keyword_completed): {e}")


# ---------------------------------------------------------------------------
# Bot Config (key/value settings stored in Supabase bot_config table)
# ---------------------------------------------------------------------------
def get_bot_config_value(key: str, default=None):
    """
    Reads a single config value from the Supabase bot_config table.
    Returns `default` if the key does not exist or on error.

    Table schema expected:
        bot_config(key TEXT PRIMARY KEY, value TEXT, updated_at TIMESTAMPTZ)
    """
    if not SUPABASE_URL:
        return default
    try:
        url = f"{SUPABASE_URL}/rest/v1/bot_config?key=eq.{key}&select=value&limit=1"
        resp = requests.get(url, headers=get_headers(), timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if data:
                return data[0].get("value", default)
    except Exception as e:
        print(f"[ERROR] DB Error (get_bot_config_value '{key}'): {e}")
    return default


def set_bot_config_value(key: str, value: str):
    """
    Upserts a key/value pair into the Supabase bot_config table.
    Creates the row if it doesn't exist, updates it if it does.
    """
    if not SUPABASE_URL:
        return
    try:
        url = f"{SUPABASE_URL}/rest/v1/bot_config"
        headers = get_headers()
        headers["Prefer"] = "resolution=merge-duplicates"
        payload = {"key": key, "value": str(value)}
        resp = requests.post(url, headers=headers, json=payload, timeout=5)
        if resp.status_code >= 400:
            print(f"[ERROR] DB Error (set_bot_config_value '{key}'): {resp.text}")
        else:
            print(f"[CONFIG] Saved '{key}' = '{value}' to Supabase bot_config.")
    except Exception as e:
        print(f"[ERROR] DB Error (set_bot_config_value '{key}'): {e}")


def get_all_bot_config() -> dict:
    """Returns the full bot_config table as a Python dict {key: value}."""
    if not SUPABASE_URL:
        return {}
    try:
        url = f"{SUPABASE_URL}/rest/v1/bot_config?select=key,value"
        resp = requests.get(url, headers=get_headers(), timeout=5)
        if resp.status_code == 200:
            return {row["key"]: row["value"] for row in resp.json()}
    except Exception as e:
        print(f"[ERROR] DB Error (get_all_bot_config): {e}")
    return {}

