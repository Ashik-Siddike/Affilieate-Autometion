import os
import sys
import requests
import json
from config import SUPABASE_URL, SUPABASE_KEY
from image_composer import compose_image

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}

def update_post_image(post_id, new_url):
    url = f"{SUPABASE_URL}/rest/v1/Post?id=eq.{post_id}"
    resp = requests.patch(url, headers=headers, json={"imageUrl": new_url})
    if resp.status_code >= 400:
        print(f"Error updating post {post_id}: {resp.text}")

def main():
    print("Fetching existing posts from Supabase...")
    url = f"{SUPABASE_URL}/rest/v1/Post?select=id,slug,title,imageUrl"
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        print("Failed to fetch posts")
        return
        
    posts = r.json()
    print(f"Found {len(posts)} posts. Reprocessing images...")
    
    for p in posts:
        post_id = p['id']
        title = p['title']
        old_url = p['imageUrl']
        slug = p['slug']
        
        print(f"\n[Processing] {slug}")
        print(f"Old URL: {old_url}")
        
        try:
            # We skip rembg if it's already an amazon image?
            # Actually, rembg will perfectly cut the watch out of the old charcoal background!
            new_url = compose_image(old_url, title)
            
            if new_url and new_url != old_url:
                update_post_image(post_id, new_url)
                print(f"✅ Updated database for {slug}!")
            else:
                print(f"⚠️ Failed to generate or upload new image for {slug}")
        except Exception as e:
            print(f"❌ Exception for {slug}: {str(e)}")

if __name__ == "__main__":
    main()
