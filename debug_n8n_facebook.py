"""
n8n Facebook Posting Debug Script
এই script দিয়ে আপনি n8n workflow-এর Facebook posting issue debug করতে পারবেন
"""

import requests
import json
from config import N8N_WEBHOOK_URL

def debug_n8n_facebook():
    """
    Debugs n8n workflow Facebook posting issue
    """
    print("="*70)
    print("🔍 n8n Facebook Posting Debug Tool")
    print("="*70)
    
    # Test payload
    test_payload = {
        "title": "Debug Test: Retro Gaming Console",
        "description": "This is a test product for debugging Facebook posting. It features excellent build quality and great performance.",
        "amazon_link": "https://automation-project.cstjpi.xyz/test-post",
        "image_url": "https://via.placeholder.com/600x400?text=Debug+Test",
        "social_caption": "🎮 Debug test post",
        "category": "Gaming",
        "long_description": "<h2>Debug Test</h2><p>This is a debug test for Facebook posting.</p>"
    }
    
    print(f"\n📡 Webhook URL: {N8N_WEBHOOK_URL}")
    print(f"\n📦 Test Payload:")
    print(json.dumps(test_payload, indent=2))
    
    print(f"\n🔄 Sending request to n8n...\n")
    
    try:
        response = requests.post(N8N_WEBHOOK_URL, json=test_payload, timeout=90)
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📋 Response Headers: {dict(response.headers)}")
        print(f"\n📄 Response Body:")
        
        try:
            response_json = response.json()
            print(json.dumps(response_json, indent=2))
            
            # Analyze response
            print(f"\n🔍 Analysis:")
            if response.status_code == 200:
                print(f"   ✅ HTTP Status: Success (200)")
                
                if isinstance(response_json, dict):
                    status = response_json.get('status', 'unknown')
                    print(f"   📊 Workflow Status: {status}")
                    
                    platforms = response_json.get('platforms_posted', [])
                    if platforms:
                        print(f"   📱 Platforms Posted: {platforms}")
                        if 'Facebook' in platforms or 'facebook' in str(platforms).lower():
                            print(f"   ✅ Facebook: Listed in platforms")
                        else:
                            print(f"   ⚠️  Facebook: NOT listed in platforms")
                    else:
                        print(f"   ⚠️  No platforms_posted field in response")
                else:
                    print(f"   ⚠️  Response is not a dictionary")
            else:
                print(f"   ❌ HTTP Status: Failed ({response.status_code})")
                
        except json.JSONDecodeError:
            print(f"   ⚠️  Response is not JSON")
            print(f"   Response text: {response.text[:500]}")
        
        print(f"\n" + "="*70)
        print(f"📋 Next Steps:")
        print(f"   1. Go to n8n Dashboard: https://ashik-mama.app.n8n.cloud")
        print(f"   2. Click on 'Executions' tab")
        print(f"   3. Find the latest execution (should be recent)")
        print(f"   4. Click on it to see detailed execution log")
        print(f"   5. Check 'Post to Facebook1' node:")
        print(f"      - Is it executed? (Green = Success, Red = Error)")
        print(f"      - Click on it to see error messages if any")
        print(f"      - Check if Facebook credentials are configured")
        print(f"      - Verify Facebook Graph API token is valid")
        print(f"   6. Check 'AI Content Transformer1' node:")
        print(f"      - Is output properly formatted?")
        print(f"      - Does it contain the message text?")
        print(f"   7. Common Issues:")
        print(f"      - Facebook token expired → Renew in n8n")
        print(f"      - Facebook page permissions missing → Add permissions")
        print(f"      - AI output format issue → Check AI node output")
        print(f"      - Network timeout → Increase timeout in workflow")
        print("="*70)
        
    except requests.exceptions.Timeout:
        print(f"❌ Request timed out after 90 seconds")
        print(f"   The workflow might be processing. Check n8n dashboard.")
    except requests.exceptions.ConnectionError:
        print(f"❌ Could not connect to n8n")
        print(f"   Check if n8n instance is running")
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"   Error type: {type(e).__name__}")

if __name__ == "__main__":
    debug_n8n_facebook()

