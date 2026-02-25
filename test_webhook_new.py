
import requests
import json
from config import N8N_WEBHOOK_URL

def test_webhook():
    print(f"Testing Webhook URL: {N8N_WEBHOOK_URL}")
    
    # Matches exact payload structure from n8n_handler.py
    payload = {
        "title": "Test Product Data",
        "description": "This is a short description for social media usage.",
        "amazon_link": "https://www.amazon.com/dp/B08H75RTZ8",
        "image_url": "https://m.media-amazon.com/images/I/61sFaHyXNCL._AC_SL1500_.jpg",
        "social_caption": "Check out this amazing product! #Affiliate #Deal",
        "category": "Electronics",
        "long_description": "<h1>Full HTML Content</h1><p>...</p>",
        
        # Flattened Social Data (Matches n8n_handler.py logic)
        "tweet": "🔥 Hot Deal: Test Product is now available! Grab it here: https://amzn.to/test #Deal",
        "pinterest_title": "Best Test Product 2026",
        "pinterest_desc": "The ultimate guide to the test product. Why you need it now.",
        "linkedin": "I recently reviewed the Test Product. It's a game changer for the industry. Read more here.",
        "facebook_content": "Just found this amazing deal! 🚀\n\nTest Product is a must-have.\n\nCheck it out here: https://amzn.to/test",
        "instagram_content": "New Review! 📸\n\nTest Product is finally here.\n\n#LinkInBio #Tech"
    }
    
    try:
        response = requests.post(N8N_WEBHOOK_URL, json=payload, timeout=20)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Connection Successful!")
        elif response.status_code == 500:
            print("❌ n8n Error (500): Workflow Execution Failed.")
        else:
            print(f"❌ Connection Failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_webhook()
