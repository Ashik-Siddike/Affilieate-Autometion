import requests
import json
import re
from config import N8N_WEBHOOK_URL

def extract_text_from_html(html_content, max_length=500):
    """
    Extracts plain text from HTML and returns a short description.
    """
    if not html_content:
        return ""
    
    # Remove script and style tags
    html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
    html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', html_content)
    
    # Clean up whitespace
    text = ' '.join(text.split())
    
    # Return first max_length characters
    if len(text) > max_length:
        return text[:max_length].rsplit(' ', 1)[0] + "..."
    return text

def trigger_n8n_workflow(title, amazon_link, image_url, social_caption, category, long_description):
    """
    Sends product data to n8n webhook for social media auto-posting.
    
    n8n workflow expects:
    - title: Product title
    - description: Short product description (extracted from long_description)
    - amazon_link: Affiliate link
    """
    # Extract short description from HTML content for n8n workflow
    description = extract_text_from_html(long_description, max_length=300)
    
    payload = {
        "title": title,
        "description": description,  # Required by n8n AI Content Transformer
        "amazon_link": amazon_link,
        "image_url": image_url,
        "social_caption": social_caption,
        "category": category,
        "long_description": long_description  # Keep full HTML for reference
    }

    try:
        print(f"📡 Sending data to n8n webhook: {N8N_WEBHOOK_URL}")
        response = requests.post(N8N_WEBHOOK_URL, json=payload, timeout=30)
        
        if response.status_code == 200:
            print(f"✅ Successfully sent data to n8n for '{title}'")
            return True
        elif response.status_code == 404:
            print(f"❌ n8n webhook not found (404)")
            print(f"   URL: {N8N_WEBHOOK_URL}")
            if "/webhook/" in N8N_WEBHOOK_URL and "/webhook-test/" not in N8N_WEBHOOK_URL:
                print(f"   💡 Hint: Production URL requires workflow to be ACTIVE in n8n")
                print(f"   💡 Or use test URL: Change /webhook/ to /webhook-test/ in config.py")
            print(f"   Response: {response.text}")
            return False
        else:
            print(f"❌ Failed to trigger n8n: {response.status_code} - {response.text}")
            return False

    except requests.exceptions.Timeout:
        print(f"❌ n8n webhook request timed out (30s)")
        return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Could not connect to n8n webhook")
        print(f"   URL: {N8N_WEBHOOK_URL}")
        print(f"   Check if n8n is running and URL is correct")
        return False
    except Exception as e:
        print(f"❌ Error triggering n8n workflow: {e}")
        return False
