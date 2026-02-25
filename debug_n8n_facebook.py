
import requests
import json
from config import N8N_WEBHOOK_URL

def test_facebook_only():
    print("🧪 Testing ONLY Facebook Posting via n8n...")
    print(f"Target: {N8N_WEBHOOK_URL}")
    
    # We send a payload that forces the workflow to use provided content
    # effectively bypassing the AI generation step if the workflow handles it correctly
    payload = {
        "title": "Facebook Debug Post",
        "description": "Debugging connection",
        "amazon_link": "https://www.google.com",
        "image_url": "https://via.placeholder.com/500",
        "social_caption": "Debug Caption",
        "category": "Debug",
        
        # KEY PART: Sending Exact Content
        "facebook_content": "🔔 Connection Test\n\nThis is a test post to verify the n8n Facebook integration is working correctly.\n\nTime: 2026-01-08",
        
        # Dummy data for others to prevent errors
        "tweet": "Test tweet",
        "pinterest_title": "Test Pin",
        "pinterest_desc": "Test Desc",
        "linkedin": "Test LI",
        "instagram_content": "Test Insta"
    }
    
    try:
        response = requests.post(N8N_WEBHOOK_URL, json=payload, timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Webhook triggered successfully.")
            print("👉 NOW: Go to n8n Executions instantly and watch the flow.")
            print("👉 If the 'Post to Facebook' node turns GREEN, check your actual Facebook Page.")
            print("👉 If it turns RED, click it to see the error.")
        else:
            print(f"❌ Webhook failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Script Error: {e}")

if __name__ == "__main__":
    test_facebook_only()
