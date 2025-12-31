import os
import json
import sqlite3
import time
import requests
from dotenv import load_dotenv

# Load env including the new Supabase keys
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Supabase credentials missing in .env")
    exit()

def get_headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates" # Upsert behavior
    }

def migrate_sites():
    print("\n🌍 Migrating Sites...")
    if not os.path.exists("sites.json"):
        print("⚠️ sites.json not found. Skipping.")
        return

    with open("sites.json", "r") as f:
        sites = json.load(f)

    url = f"{SUPABASE_URL}/rest/v1/sites"
    
    for site in sites:
        data = {
            "name": site.get("name"),
            "url": site.get("url"),
            "username": site.get("username"),
            "app_password": site.get("app_password"),
            "n8n_webhook": site.get("n8n_webhook"),
            "keywords": site.get("keywords", [])
        }
        
        try:
            # We use POST with resolution=merge-duplicates (requires PK conflict, but 'sites' PK is ID (auto))
            # Since we can't easily upsert on 'url' without a unique constraint, we'll check first.
            
            # 1. Check if exists (by URL)
            check_url = f"{SUPABASE_URL}/rest/v1/sites?url=eq.{site.get('url')}&select=id"
            check_res = requests.get(check_url, headers=get_headers())
            
            if check_res.json():
                print(f"⚠️ Site already exists: {site['name']}")
                continue
            
            # 2. Insert
            response = requests.post(url, headers=get_headers(), json=data)
            if response.status_code < 400:
                print(f"✅ Migrated site: {site['name']}")
            else:
                print(f"❌ API Error for {site['name']}: {response.text}")
                
        except Exception as e:
            print(f"❌ Failed to migrate site {site['name']}: {e}")

def migrate_products():
    print("\n📦 Migrating Products...")
    if not os.path.exists("amazon_products.db"):
        print("⚠️ amazon_products.db not found. Skipping.")
        return

    conn = sqlite3.connect("amazon_products.db")
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT * FROM products")
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
        
        print(f"Found {len(rows)} products in SQLite.")
        
        batch_size = 50
        batch = []
        
        api_url = f"{SUPABASE_URL}/rest/v1/products"
        
        for row in rows:
            product = dict(zip(columns, row))
            
            is_pub = product.get('is_published')
            if isinstance(is_pub, int):
                is_pub = bool(is_pub)
                
            item = {
                "asin": product.get("asin"),
                "title": product.get("title"),
                "price": product.get("price"),
                "rating": product.get("rating"),
                "review_count": product.get("review_count"),
                "image_url": product.get("image_url"),
                "product_url": product.get("product_url"),
                "is_published": is_pub,
                "post_link": product.get("post_link", None),
            }
            if 'post_link' in product:
                item['post_link'] = product['post_link']
            
            batch.append(item)
            
            if len(batch) >= batch_size:
                try:
                    # Supabase REST Bulk Insert
                    headers = get_headers()
                    response = requests.post(api_url, headers=headers, json=batch)
                    
                    if response.status_code < 400:
                        print(f"✅ Uploaded batch of {len(batch)}")
                    else:
                        print(f"❌ Batch API Error: {response.text}")
                    
                    batch = []
                except Exception as e:
                    print(f"❌ Batch error: {e}")
        
        if batch:
            try:
                headers = get_headers()
                response = requests.post(api_url, headers=headers, json=batch)
                if response.status_code < 400:
                    print(f"✅ Uploaded final batch of {len(batch)}")
                else:
                    print(f"❌ Final Batch API Error: {response.text}")
            except Exception as e:
                print(f"❌ Final batch error: {e}")
                
    except Exception as e:
        print(f"❌ SQLite error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_sites()
    migrate_products()
    print("\n✨ Migration Complete!")
