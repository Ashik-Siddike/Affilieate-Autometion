import os
import sys
import requests
import json
import asyncio
from config import SUPABASE_URL, SUPABASE_KEY
from image_composer import compose_image

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}

async def main():
    print("Fetching published products with post links...")
    url = f"{SUPABASE_URL}/rest/v1/products?is_published=eq.true&post_link=not.is.null&select=image_url,post_link,title"
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        print("Failed to fetch products")
        return
        
    products = r.json()
    print(f"Found {len(products)} published products to fix.")
    
    # We will use raw Supabase REST to update Posts
    for p in products:
        raw_amazon_url = p.get('image_url')
        post_link = p.get('post_link')
        title = p.get('title')
        
        if not raw_amazon_url or not post_link:
            continue
            
        # extract slug from post_link (https://whitlogic.online/watch-reviews/slug)
        slug = post_link.rstrip('/').split('/')[-1]
        
        print(f"\n[Fixing] {slug}")
        print(f"Original Amazon URL: {raw_amazon_url}")
        
        try:
            # Recompose using original amazon image!
            new_url = compose_image(raw_amazon_url, title)
            
            if new_url and new_url != raw_amazon_url:
                # Update Post table via REST
                update_url = f"{SUPABASE_URL}/rest/v1/Post?slug=eq.{slug}"
                resp = requests.patch(update_url, headers=headers, json={"imageUrl": new_url})
                if resp.status_code < 400:
                    print(f"✅ Fixed image for {slug}!")
                else:
                    print(f"⚠️ Failed to update DB for {slug}: {resp.text}")
            else:
                print(f"⚠️ Failed to generate new image for {slug}")
        except Exception as e:
            print(f"❌ Exception for {slug}: {str(e)}")
            
    print("Done fixing images!")

if __name__ == "__main__":
    asyncio.run(main())
