import os
import requests
import random
import json
from config import SUPABASE_URL, SUPABASE_KEY

# Headers for Supabase REST API
def get_headers():
    if not SUPABASE_URL or not SUPABASE_KEY:
        return {}
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"  # Return data after insert/update
    }

def init_db():
    """Confirms connection to Supabase via REST API."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("⚠️ Supabase credentials missing.")
        return
    try:
        # Simple ping: Fetch 1 item from products
        url = f"{SUPABASE_URL}/rest/v1/products?select=count&limit=1"
        response = requests.get(url, headers=get_headers(), timeout=5)
        if response.status_code == 200:
            print("✅ Connected to Supabase (REST).")
        else:
            print(f"❌ Supabase connection error: {response.text}")
    except Exception as e:
        print(f"❌ Supabase connection error: {e}")

def check_product_status(asin):
    """
    Checks product status.
    Returns:
        None if not exists
        0 if exists but not published
        1 if exists and published
    """
    if not SUPABASE_URL: return None
    try:
        url = f"{SUPABASE_URL}/rest/v1/products?asin=eq.{asin}&select=is_published"
        response = requests.get(url, headers=get_headers(), timeout=10)
        data = response.json()
        
        if data and len(data) > 0:
            return 1 if data[0].get('is_published') else 0
        return None
    except Exception as e:
        print(f"DB Error (check_status): {e}")
        return None

def save_product(data_dict):
    """Saves a new product to the database (Upsert)."""
    if not SUPABASE_URL: return
    try:
        url = f"{SUPABASE_URL}/rest/v1/products"
        data = {
            "asin": data_dict.get('asin'),
            "title": data_dict.get('title'),
            "price": data_dict.get('price'),
            "rating": data_dict.get('rating'),
            "review_count": data_dict.get('review_count'),
            "image_url": data_dict.get('image_url'),
            "product_url": data_dict.get('product_url'),
        }
        
        # Upsert: explicit "on_conflict" handling logic via Prefer header
        # Supabase defaults to fail on duplicate PK if not specified.
        # Ideally use POST with Prefer: resolution=merge-duplicates
        headers = get_headers()
        headers["Prefer"] = "resolution=merge-duplicates"
        
        response = requests.post(url, headers=headers, json=data, timeout=10)
        if response.status_code >= 400:
            print(f"DB Error (save_product): {response.text}")
            
    except Exception as e:
        print(f"DB Error (save_product): {e}")

def mark_as_published(asin):
    """Marks a product as published."""
    if not SUPABASE_URL: return
    try:
        url = f"{SUPABASE_URL}/rest/v1/products?asin=eq.{asin}"
        requests.patch(url, headers=get_headers(), json={'is_published': True})
    except Exception as e:
        print(f"DB Error (mark_published): {e}")

def get_similar_products(current_asin, limit=2):
    """
    Fetches random other products.
    """
    if not SUPABASE_URL: return []
    try:
        # Fetch 20, same logic as before
        url = f"{SUPABASE_URL}/rest/v1/products?asin=neq.{current_asin}&select=title,price,rating,review_count,image_url,product_url&limit=20"
        response = requests.get(url, headers=get_headers())
        products = response.json()
        
        if not products: return []
        
        if len(products) > limit:
            return random.sample(products, limit)
        return products
    except Exception as e:
        print(f"DB Error (similar): {e}")
        return []

def get_published_posts(limit=5):
    """Fetches a list of recently published posts."""
    if not SUPABASE_URL: return []
    try:
        request_headers = get_headers()
        # Filter where post_link is not null
        url = f"{SUPABASE_URL}/rest/v1/products?is_published=eq.true&post_link=not.is.null&select=title,post_link&order=created_at.desc&limit={limit}"
        response = requests.get(url, headers=request_headers)
        data = response.json()
        
        return [{'title': p['title'], 'link': p['post_link']} for p in data]
    except Exception as e:
        print(f"DB Error (get_posts): {e}")
        return []

def get_relevant_posts(keyword, limit=5):
    """
    Fetches contextually relevant posts for internal linking (Silo).
    Searches for published posts where title contains the keyword.
    """
    if not SUPABASE_URL: return []
    try:
        request_headers = get_headers()
        # Basic full-text search simulation using ilike on title
        # keyword usually is "Best Gaming Laptop", we want to match "Gaming Laptop"
        # Let's simple split and take the noun or just use the full keyword
        # Safe approach: ilike %keyword%
        
        # Clean keyword slightly
        clean_kw = keyword.replace(' ', '%') 
        
        url = f"{SUPABASE_URL}/rest/v1/products?is_published=eq.true&post_link=not.is.null&title=ilike.*{clean_kw}*&select=title,post_link&order=created_at.desc&limit={limit}"
        response = requests.get(url, headers=request_headers)
        data = response.json()
        
        # Fallback to recent if specific not found (Simulate Silo filling)
        if not data or len(data) < 2:
             print("⚠️ No direct relevant links found. Mixing with recent posts.")
             recent = get_published_posts(limit=limit)
             # Merge unique
             existing_links = {p['post_link'] for p in data} if data else set()
             for r in recent:
                 if r['link'] not in existing_links and len(data) < limit:
                     data.append({'title': r['title'], 'post_link': r['link']})
        
        return [{'title': p['title'], 'link': p['post_link']} for p in data]
    except Exception as e:
        print(f"DB Error (get_relevant_posts): {e}")
        return get_published_posts(limit)

def update_post_link(asin, post_link):
    """Updates the post_link for a published product."""
    if not SUPABASE_URL: return
    try:
        url = f"{SUPABASE_URL}/rest/v1/products?asin=eq.{asin}"
        requests.patch(url, headers=get_headers(), json={'post_link': post_link})
    except Exception as e:
        print(f"DB Error (update_link): {e}")


