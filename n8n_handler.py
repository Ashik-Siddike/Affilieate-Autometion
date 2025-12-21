import requests
import json

# n8n Webhook URL provided by user
N8N_WEBHOOK_URL = "https://ashik-mama.app.n8n.cloud/webhook/amazon-master-webhook"

def trigger_n8n_workflow(title, amazon_link, image_url, social_caption, category, long_description):
    """
    Sends product data to n8n webhook for social media auto-posting.
    """
    payload = {
        "title": title,
        "amazon_link": amazon_link,
        "image_url": image_url,
        "social_caption": social_caption,
        "category": category,
        "long_description": long_description
    }

    try:
        response = requests.post(N8N_WEBHOOK_URL, json=payload)
        
        if response.status_code == 200:
            print(f"✅ Successfully sent data to n8n for '{title}'")
            return True
        else:
            print(f"❌ Failed to trigger n8n: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        print(f"❌ Error triggering n8n workflow: {e}")
        return False
