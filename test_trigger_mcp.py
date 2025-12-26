"""
MCP Test Script - Check if n8n workflow triggers properly
"""
import requests
import json
from config import N8N_WEBHOOK_URL

print("="*70)
print("Testing n8n Workflow Trigger via MCP")
print("="*70)

# Test payload matching what our code sends
test_payload = {
    "title": "MCP Test: Retro Gaming Console",
    "description": "This is a test from MCP to verify workflow triggers correctly. Testing Facebook posting functionality.",
    "amazon_link": "https://automation-project.cstjpi.xyz/test-post-mcp",
    "image_url": "https://via.placeholder.com/600x400?text=MCP+Test",
    "social_caption": "🎮 MCP Test Post - Check if workflow triggers",
    "category": "Gaming",
    "long_description": "<h2>MCP Test Product</h2><p>This is a test product to verify n8n workflow triggering and Facebook posting.</p>"
}

print(f"\n[1] Webhook URL: {N8N_WEBHOOK_URL}")
print(f"\n[2] Payload:")
print(json.dumps(test_payload, indent=2))

print(f"\n[3] Sending request...\n")

try:
    response = requests.post(N8N_WEBHOOK_URL, json=test_payload, timeout=90)
    
    print(f"[4] Status Code: {response.status_code}")
    print(f"[5] Response Headers:")
    for key, value in response.headers.items():
        if key.lower() in ['content-type', 'content-length']:
            print(f"   {key}: {value}")
    
    print(f"\n[6] Response Body:")
    try:
        response_json = response.json()
        print(json.dumps(response_json, indent=2))
        
        # Analyze
        print(f"\n[7] Analysis:")
        if response.status_code == 200:
            print(f"   [SUCCESS] HTTP Request: SUCCESS")
            if isinstance(response_json, dict):
                status = response_json.get('status', 'unknown')
                print(f"   [INFO] Workflow Status: {status}")
                
                platforms = response_json.get('platforms_posted', [])
                if platforms:
                    print(f"   [INFO] Platforms: {platforms}")
                else:
                    print(f"   [WARNING] No platforms_posted in response")
            print(f"\n   [NEXT STEPS]:")
            print(f"      1. Go to n8n dashboard: https://ashik-mama.app.n8n.cloud")
            print(f"      2. Check 'Executions' tab")
            print(f"      3. Find this execution (should be recent)")
            print(f"      4. Check each node:")
            print(f"         - Amazon-Master-Webhook1: Should be Green")
            print(f"         - AI Content Transformer1: Should be Green")
            print(f"         - Post to Facebook1: Check if Green or Red")
            print(f"      5. If Post to Facebook1 is Red:")
            print(f"         - Click on it to see error")
            print(f"         - Check Facebook credentials")
            print(f"         - Verify Facebook token is valid")
        else:
            print(f"   [FAILED] HTTP Request: FAILED ({response.status_code})")
            
    except json.JSONDecodeError:
        print(f"   [WARNING] Response is not JSON")
        print(f"   Response text: {response.text[:500]}")
        
except requests.exceptions.Timeout:
    print(f"[ERROR] Request timed out after 90 seconds")
    print(f"   -> Workflow might be processing")
    print(f"   -> Check n8n dashboard for execution")
except requests.exceptions.ConnectionError:
    print(f"[ERROR] Connection failed")
    print(f"   -> Check if n8n instance is running")
    print(f"   -> Verify URL is correct")
except Exception as e:
    print(f"[ERROR] Error: {e}")

print("\n" + "="*70)

