import requests
import time
from config import NEXT_API_URL, BOT_API_SECRET

def ping_google_sitemap():
    """Pings Google to notify that the sitemap has been updated."""
    try:
        sitemap_url = "https://whitlogic.online/sitemap.xml"
        ping_url = f"https://www.google.com/ping?sitemap={sitemap_url}"
        response = requests.get(ping_url, timeout=10)
        if response.status_code == 200:
            print(f" [SEO] Successfully pinged Google with new sitemap.")
        else:
            print(f" [SEO] Google ping returned status {response.status_code}")
    except Exception as e:
        print(f" [SEO] Error pinging Google: {e}")

def publish_to_nextjs_with_retry(post_data, headers, max_retries=3):
    """
    Attempts to publish to Next.js API with exponential backoff on failure.
    """
    for attempt in range(max_retries):
        try:
            print(f" Publishing to Next.js API: {NEXT_API_URL} (Attempt {attempt + 1}/{max_retries})")
            response = requests.post(NEXT_API_URL, json=post_data, headers=headers, timeout=15)
            
            if response.status_code in [200, 201]:
                return response
            elif response.status_code == 429:
                print(f" Rate limited by Next.js API. Retrying...")
            else:
                print(f" Failed to create post: {response.status_code} - {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f" Network error publishing post: {e}")
            
        if attempt < max_retries - 1:
            backoff_time = (2 ** attempt) * 2  # 2s, 4s, 8s...
            print(f" Waiting {backoff_time}s before retry...")
            time.sleep(backoff_time)
            
    return None

def detect_category(title: str, keyword: str = '') -> str:
    """Auto-detects category from product title and keyword."""
    text = (title + ' ' + keyword).lower()
    if any(w in text for w in ['waterproof', 'water resistant', 'dive', 'swimming', '200m', '100m', '50m', 'atm']):
        return 'waterproof'
    if any(w in text for w in ['under 20', 'under $20', 'budget', 'cheap', 'affordable', 'value']):
        return 'budget-under-20'
    if any(w in text for w in ['digital', 'led', 'lcd', 'electronic', 'alarm']):
        return 'digital'
    if any(w in text for w in ['military', 'army', 'tactical', 'outdoor', 'hiking', 'camping', 'survival']):
        return 'tactical'
    if any(w in text for w in ['sport', 'running', 'fitness', 'gym', 'workout', 'chronograph']):
        return 'sports'
    return 'tactical'


def publish_post(title, slug, content, image_url, model_number, brand, amazon_link, faqs=None, keyword=''):
    """
    Creates a new post via the Next.js Custom API endpoint.
    """
    try:
        headers = {
            'Content-Type': 'application/json',
            'x-bot-api-secret': BOT_API_SECRET
        }
        
        post_data = {
            'title': title,
            'slug': slug,
            'content': content,
            'imageUrl': image_url,
            'modelNumber': model_number,
            'brand': brand,
            'amazonAffiliateLink': amazon_link,
        }

        if faqs:
            post_data['faqs'] = faqs
        
        response = publish_to_nextjs_with_retry(post_data, headers)
        
        if response and response.status_code in [200, 201]:
            print(f" Post published successfully: {title}")
            slug = response.json().get('slug')
            full_url = f"https://whitlogic.online/watch-reviews/{slug}"
            
            # Ping Google after successful publish
            ping_google_sitemap()
            
            return full_url, image_url
        else:
            return None, None

    except Exception as e:
        print(f" Error publishing post: {e}")
        return None, None
