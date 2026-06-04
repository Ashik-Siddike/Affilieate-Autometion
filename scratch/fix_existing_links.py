import os
import requests
import json
from dotenv import load_dotenv

# Load env variables from root
load_dotenv(dotenv_path="../.env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
TARGET_TAG = "ashiksiddike-20"

if not SUPABASE_URL or not SUPABASE_KEY:
    # Try local directory .env as fallback
    load_dotenv()
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")

print(f"Supabase URL: {SUPABASE_URL}")
print(f"Tracking Tag to ensure: {TARGET_TAG}")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("[ERROR] Supabase credentials not found!")
    exit(1)

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

def fix_links():
    # 1. Fetch all posts from the Post table
    url = f"{SUPABASE_URL}/rest/v1/Post?select=id,title,amazonAffiliateLink"
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"[ERROR] Failed to fetch posts: {response.text}")
        return
        
    posts = response.json()
    print(f"Found {len(posts)} total posts to review.")
    
    fixed_count = 0
    skipped_count = 0
    
    for post in posts:
        post_id = post.get("id")
        title = post.get("title")
        link = post.get("amazonAffiliateLink")
        
        if not link:
            print(f"[-] Skipped: '{title}' (No Amazon link found)")
            skipped_count += 1
            continue
            
        # Check if tracking tag is already in the link
        if f"tag={TARGET_TAG}" in link:
            print(f"[✓] Already correct: '{title}' -> {link}")
            skipped_count += 1
            continue
            
        # Link needs fixing. Build correct affiliate link
        # Clean existing tracking parameters if any different tag is present, otherwise just append
        # If it has some other tag, or none, let's append our tag
        sep = "&" if "?" in link else "?"
        
        # Remove any existing trailing spaces or tags if we want to be safe, but usually it's just raw
        new_link = f"{link}{sep}tag={TARGET_TAG}"
        
        # Double check to prevent double '?' or double 'tag='
        if link.endswith("?") or link.endswith("&"):
            new_link = f"{link}tag={TARGET_TAG}"
            
        print(f"[+] Fixing: '{title}'")
        print(f"    Old: {link}")
        print(f"    New: {new_link}")
        
        # 2. Update the link in Supabase
        update_url = f"{SUPABASE_URL}/rest/v1/Post?id=eq.{post_id}"
        update_payload = {"amazonAffiliateLink": new_link}
        
        patch_response = requests.patch(update_url, headers=headers, json=update_payload)
        
        if patch_response.status_code in [200, 201, 204]:
            print(f"    [SUCCESS] Updated link successfully.")
            fixed_count += 1
        else:
            print(f"    [ERROR] Failed to update: {patch_response.text}")
            
    print("\n" + "="*50)
    print("FINISHED RUNNING REPAIR SCRIPT")
    print(f"Total Reviewed: {len(posts)}")
    print(f"Total Fixed   : {fixed_count}")
    print(f"Total Skipped : {skipped_count}")
    print("="*50)

if __name__ == "__main__":
    fix_links()
