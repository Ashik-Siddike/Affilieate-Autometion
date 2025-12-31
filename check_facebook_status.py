"""
Quick Facebook Posting Status Checker
এই script দিয়ে আপনি quickly check করতে পারবেন Facebook posting issue কি
"""

import requests
import json
from config import N8N_WEBHOOK_URL

def check_facebook_status():
    """
    Quick check for Facebook posting status
    """
    print("="*70)
    print("🔍 Facebook Posting Status Checker")
    print("="*70)
    
    # Check 1: Webhook URL
    print(f"\n1️⃣  Webhook URL Check:")
    print(f"   URL: {N8N_WEBHOOK_URL}")
    if "ashik-mama.app.n8n.cloud" in N8N_WEBHOOK_URL:
        print(f"   ✅ URL looks correct")
    else:
        print(f"   ⚠️  URL might be incorrect")
    
    # Check 2: Test Connection
    print(f"\n2️⃣  Connection Test:")
    try:
        # Just test if webhook is reachable (don't send full payload)
        test_response = requests.get(N8N_WEBHOOK_URL.replace("/webhook/", "/health"), timeout=5)
        print(f"   ✅ n8n instance is reachable")
    except:
        try:
            # Try actual webhook with minimal payload
            test_payload = {"test": True}
            response = requests.post(N8N_WEBHOOK_URL, json=test_payload, timeout=10)
            if response.status_code in [200, 404, 400]:
                print(f"   ✅ Webhook is responding (Status: {response.status_code})")
            else:
                print(f"   ⚠️  Webhook returned status: {response.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Cannot connect to n8n")
            print(f"      → Check if n8n instance is running")
            print(f"      → Verify URL is correct")
        except Exception as e:
            print(f"   ⚠️  Connection test failed: {e}")
    
    # Check 3: Send Test Request
    print(f"\n3️⃣  Sending Test Request:")
    test_payload = {
        "title": "Status Check Test",
        "description": "This is a status check test",
        "amazon_link": "https://example.com/test",
        "image_url": "https://via.placeholder.com/600",
        "social_caption": "Test",
        "category": "Test",
        "long_description": "<p>Test</p>"
    }
    
    try:
        print(f"   Sending test payload...")
        response = requests.post(N8N_WEBHOOK_URL, json=test_payload, timeout=30)
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print(f"   ✅ Request successful!")
            try:
                response_data = response.json()
                print(f"   Response: {json.dumps(response_data, indent=2)}")
            except:
                print(f"   Response: {response.text[:200]}")
        elif response.status_code == 404:
            print(f"   ❌ Webhook not found (404)")
            print(f"      → Check if workflow is ACTIVE in n8n")
            print(f"      → Verify webhook path is correct")
        else:
            print(f"   ⚠️  Unexpected status: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            
    except requests.exceptions.Timeout:
        print(f"   ⚠️  Request timed out")
        print(f"      → Workflow might be processing")
        print(f"      → Check n8n dashboard for execution")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Summary
    print(f"\n" + "="*70)
    print(f"📋 Summary & Next Steps:")
    print(f"="*70)
    print(f"\n✅ If all checks passed:")
    print(f"   1. Go to n8n dashboard: https://ashik-mama.app.n8n.cloud")
    print(f"   2. Check 'Executions' tab for latest execution")
    print(f"   3. Verify 'Post to Facebook1' node is Green")
    print(f"   4. Check your Facebook page for the post")
    
    print(f"\n❌ If checks failed:")
    print(f"   1. Run detailed debug: python debug_n8n_facebook.py")
    print(f"   2. Check troubleshooting guide: FACEBOOK_TROUBLESHOOTING.md")
    print(f"   3. Verify Facebook credentials in n8n workflow")
    
    print(f"\n💡 Common Issues:")
    print(f"   - Facebook token expired → Renew in n8n credentials")
    print(f"   - Workflow not active → Toggle ON in n8n dashboard")
    print(f"   - Facebook permissions missing → Add in Facebook Developer Portal")
    print(f"   - AI output issue → Check 'AI Content Transformer1' node")
    
    print("="*70)

if __name__ == "__main__":
    check_facebook_status()


