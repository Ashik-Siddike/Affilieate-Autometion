import requests
import json

# Test n8n webhook connection
def test_n8n_connection():
    """
    Tests if the n8n webhook is reachable and responding correctly.
    """
    webhook_url = "https://ashik-mama.app.n8n.cloud/webhook/amazon-master-webhook"
    
    test_payload = {
        "title": "Test Product - Gaming Headset",
        "amazon_link": "https://example.com/test-post",
        "image_url": "https://via.placeholder.com/600x400",
        "social_caption": "🎮 Testing our automation! This is an amazing gaming headset. #gaming #tech #review",
        "category": "Gaming Accessories",
        "long_description": "<h2>Test Product Review</h2><p>This is a test article to verify our n8n workflow integration. The product features include excellent sound quality, comfortable design, and amazing battery life.</p>"
    }
    
    print("🔄 Testing n8n webhook connection...")
    print(f"📡 Webhook URL: {webhook_url}")
    print(f"📦 Payload: {json.dumps(test_payload, indent=2)}")
    print("\n" + "="*60 + "\n")
    
    try:
        response = requests.post(webhook_url, json=test_payload, timeout=90)
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📝 Response Headers: {dict(response.headers)}")
        print(f"📄 Response Body: {response.text[:500]}")  # First 500 chars
        
        if response.status_code == 200:
            print("\n✅ SUCCESS! Webhook is working correctly.")
            try:
                response_json = response.json()
                print(f"✨ Response JSON: {json.dumps(response_json, indent=2)}")
            except:
                print("ℹ️  Response is not JSON format")
            return True
        else:
            print(f"\n❌ FAILED! Status code: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ ERROR: Request timed out. n8n might be slow or unavailable.")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Could not connect to n8n. Check if:")
        print("   1. n8n is running")
        print("   2. Cloudflare tunnel is active")
        print("   3. Workflow is activated in n8n")
        return False
    except Exception as e:
        print(f"❌ ERROR: {type(e).__name__}: {e}")
        return False

if __name__ == "__main__":
    success = test_n8n_connection()
    
    if success:
        print("\n" + "="*60)
        print("🎉 n8n Integration Test PASSED!")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("⚠️  n8n Integration Test FAILED!")
        print("Please check:")
        print("  1. Is n8n running? (n8n start)")
        print("  2. Is Cloudflare tunnel active?")
        print("  3. Is the workflow activated in n8n UI?")
        print("  4. Are all credentials configured?")
        print("="*60)
