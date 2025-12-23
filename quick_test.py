import requests
import json

webhook_url = "https://ashiksissike-n8n-free.hf.space/webhook-test/amazon-master-webhook"

test_payload = {
    "title": "Test Product",
    "amazon_link": "https://example.com/test",
    "image_url": "https://via.placeholder.com/600",
    "social_caption": "Test caption",
    "category": "Test Category",
    "long_description": "Test description"
}

print("Testing webhook...")
try:
    response = requests.post(webhook_url, json=test_payload, timeout=90)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:500]}")
except Exception as e:
    print(f"Error: {e}")
