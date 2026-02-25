import requests
import json
import time
from config import MAKE_WEBHOOK_URL

def send_to_make_webhook(payload, webhook_url=None):
    """
    Sends the article data and social content to Make.com webhook.
    
    Args:
        payload (dict): The data to send.
        webhook_url (str, optional): Override default webhook URL.
            
    Returns:
        bool: True if successful, False otherwise.
    """
    # Use provided URL or fallback to config
    target_url = webhook_url if webhook_url else MAKE_WEBHOOK_URL
    
    if not target_url:
        print("❌ Error: MAKE_WEBHOOK_URL is not set and no site-specific URL provided.")
        return False

    print(f"🚀 Sending data to Make.com Webhook: {target_url}")
    
    # Ensure payload is JSON compatible
    try:
        # Debug: Print payload keys
        print(f"📦 Payload keys: {list(payload.keys())}")
        
        headers = {
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            target_url, 
            json=payload, 
            headers=headers, 
            timeout=30 # 30 seconds timeout
        )
        
        if response.status_code == 200:
            print("✅ Successfully sent data to Make.com!")
            return True
        else:
            print(f"⚠️ Make.com Webhook Failed! Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Error: Connection to Make.com timed out.")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Error sending data to Make.com: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error in make_handler: {e}")
        return False
