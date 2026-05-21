import os
import random
import requests
import json
from config import SUPABASE_URL, SUPABASE_KEY
from ai_content_generator import generate_content
import datetime
import uuid

def get_headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

def fetch_random_posts(limit=2):
    url = f"{SUPABASE_URL}/rest/v1/Post?select=id,title,brand,modelNumber,imageUrl,category,amazonAffiliateLink&isVsArticle=eq.false"
    res = requests.get(url, headers=get_headers())
    if res.status_code == 200:
        posts = res.json()
        if len(posts) >= limit:
            return random.sample(posts, limit)
    return None

def compose_vs_image(img_url1, img_url2):
    # For simplicity, we just return the first image or upload a custom one.
    # A true PIL implementation would download both, crop, and stitch.
    # Here, we'll just use the first image url.
    return img_url1

def create_vs_article():
    print("[INFO] Fetching candidates for VS Article...")
    candidates = fetch_random_posts(2)
    if not candidates:
        print("[ERROR] Not enough posts for VS comparison.")
        return

    post1, post2 = candidates
    print(f"[INFO] Selected: {post1['title']} VS {post2['title']}")

    prompt = f"""
    You are an expert watch reviewer. Write a comprehensive "Versus" comparison article between the {post1['brand']} {post1['modelNumber']} and the {post2['brand']} {post2['modelNumber']}.
    The article must be formatted in HTML (only the inside of the body). Do not use markdown backticks.
    Use headings like H2, H3, bold text, and lists.
    Include these sections:
    - Introduction
    - Design & Build Quality
    - Features & Performance
    - Value for Money
    - Final Verdict (declare a winner!)
    """
    
    print("[INFO] Generating AI content...")
    content = generate_content(prompt)
    if not content:
        print("[ERROR] AI generation failed.")
        return

    # Clean HTML markdown
    content = content.replace("```html", "").replace("```", "").strip()

    title = f"{post1['brand']} {post1['modelNumber']} vs {post2['brand']} {post2['modelNumber']}: Which is Better?"
    slug = title.lower().replace(" ", "-").replace(":", "").replace("&", "and").replace("?", "")
    
    # Combined affiliate link trick (e.g. separate by comma or just use post1's)
    # We will just use post1's link for simplicity, but in a real scenario you might embed both in HTML.
    content += f"<p><br><strong>Get the {post1['brand']} here:</strong> <a href='{post1['amazonAffiliateLink']}' target='_blank'>Amazon Link</a></p>"
    content += f"<p><strong>Get the {post2['brand']} here:</strong> <a href='{post2['amazonAffiliateLink']}' target='_blank'>Amazon Link</a></p>"

    # Insert into database
    new_post = {
        "id": str(uuid.uuid4()),
        "title": title,
        "slug": slug,
        "content": content,
        "amazonAffiliateLink": post1['amazonAffiliateLink'], # Fallback
        "imageUrl": post1['imageUrl'], # Just use post1 image for now
        "brand": f"{post1['brand']} & {post2['brand']}",
        "modelNumber": "VS",
        "category": post1['category'],
        "isVsArticle": True,
        "tags": ["vs", "comparison", post1['brand'], post2['brand']],
        "isDeal": False,
        "ratingValue": 4.5,
        "ratingCount": 100
    }

    print("[INFO] Saving to Supabase...")
    url = f"{SUPABASE_URL}/rest/v1/Post"
    res = requests.post(url, headers=get_headers(), json=new_post)
    if res.status_code in [200, 201]:
        print(f"[SUCCESS] VS Article created: {title}")
    else:
        print(f"[ERROR] Failed to save VS Article: {res.text}")

if __name__ == "__main__":
    create_vs_article()
