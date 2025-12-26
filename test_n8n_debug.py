import requests
import json
from config import N8N_WEBHOOK_URL

def test_n8n_connection():
    print(f"📡 Testing n8n Webhook Connection...")
    print(f"🔗 URL: {N8N_WEBHOOK_URL}")

    payload = {
        "title": "Test Product Title",
        "description": "This is a test description for debugging.",
        "amazon_link": "https://example.com/product",
        "image_url": "https://via.placeholder.com/150",
        "social_caption": "Test caption for social media #test",
        "category": "Debugging",
        "long_description": "<p>This is a full HTML description to test parsing.</p>"
    }

    try:
        response = requests.post(N8N_WEBHOOK_URL, json=payload, timeout=10)
        
        print(f"\n✅ Status Code: {response.status_code}")
        print(f"📄 Response Text: {response.text}")
        
        if response.status_code == 200:
            print("\n🎉 Connection Successful! Check your n8n execution logs.")
        elif response.status_code == 404:
            print("\n❌ Error 404: Webhook not found.")
            print("👉 Check if your n8n workflow is ACTIVE.")
            print("👉 Check if the URL matches your n8n Production URL.")
        else:
            print(f"\n❌ Unexpected Error: {response.status_code}")

    except Exception as e:
        print(f"\n❌ Connection Failed: {e}")

if __name__ == "__main__":
    test_n8n_connection()
