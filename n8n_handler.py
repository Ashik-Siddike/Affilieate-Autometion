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

def trigger_n8n_workflow(title, amazon_link, image_url, social_caption, category, long_description, webhook_url=None):
    """
    Sends product data to n8n webhook for social media auto-posting.
    
    n8n workflow expects:
    - title: Product title
    - description: Short product description (extracted from long_description)
    - amazon_link: Affiliate link
    """
    # Use provided webhook or fallback to config
    target_url = webhook_url if webhook_url else N8N_WEBHOOK_URL
    
    # Extract short description from HTML content for n8n workflow
    description = extract_text_from_html(long_description, max_length=300)
    
    # Ensure description is not empty
    if not description or len(description) < 10:
        description = f"Check out this amazing product: {title}. It's a top-rated choice in {category}. Click the link to learn more!"

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
        print(f"📡 Sending data to n8n webhook: {target_url}")
        print(f"   Payload: title='{title[:50]}...', description='{description[:50]}...'")
        
        response = requests.post(target_url, json=payload, timeout=90)  # Increased timeout for AI processing
        
        if response.status_code == 200:
            try:
                response_data = response.json()
                print(f"✅ Successfully sent data to n8n for '{title}'")
                print(f"📋 n8n Response: {json.dumps(response_data, indent=2)}")
                
                # Check if Facebook posting was successful
                if isinstance(response_data, dict):
                    if response_data.get('status') == 'complete':
                        platforms = response_data.get('platforms_posted', [])
                        if 'Facebook' in platforms or 'facebook' in str(platforms).lower():
                            print(f"✅ Facebook post published successfully!")
                            return True
                        else:
                            print(f"⚠️  Workflow completed but Facebook status unclear")
                            print(f"   Platforms in response: {platforms}")
                            print(f"   💡 Check n8n dashboard Executions tab for Facebook node errors")
                            print(f"   💡 Verify Facebook credentials in n8n workflow")
                            return True  # Workflow executed but Facebook might have failed
                    else:
                        print(f"⚠️  Workflow response: {response_data}")
                        print(f"   💡 Check n8n dashboard for execution details")
                        return True
                else:
                    print(f"✅ n8n workflow executed successfully")
                    print(f"   💡 Check n8n dashboard to verify Facebook post was published")
                    return True
            except json.JSONDecodeError:
                # Response is not JSON, but status is 200
                response_text = response.text.strip()
                
                if not response_text or len(response_text) == 0:
                    # Empty response - workflow triggered but response node might not be configured properly
                    print(f"⚠️  n8n workflow triggered but received empty response")
                    print(f"   This usually means:")
                    print(f"   1. Workflow is processing (AI might be generating content)")
                    print(f"   2. Response node might not be properly configured")
                    print(f"   3. Workflow execution might still be running")
                    print(f"\n   💡 IMPORTANT: Check n8n dashboard immediately:")
                    print(f"      → Go to: https://ashik-mama.app.n8n.cloud")
                    print(f"      → Click 'Executions' tab")
                    print(f"      → Find latest execution (should be recent)")
                    print(f"      → Check execution status:")
                    print(f"         - If 'Running': Wait for it to complete")
                    print(f"         - If 'Success': Check 'Post to Facebook1' node")
                    print(f"         - If 'Error': Click to see error details")
                    print(f"      → Click on 'Post to Facebook1' node to see:")
                    print(f"         - If Green: Post was sent (check Facebook page)")
                    print(f"         - If Red: Click to see error (likely Facebook token issue)")
                    return True  # Workflow triggered, but need to check dashboard
                else:
                    print(f"✅ n8n workflow executed successfully (non-JSON response)")
                    print(f"   Response text: {response_text[:200]}")
                    print(f"   💡 Check n8n dashboard Executions tab to verify Facebook posting")
                    return True
                
        elif response.status_code == 404:
            print(f"❌ n8n webhook not found (404)")
            print(f"   URL: {target_url}")
            if "/webhook/" in target_url and "/webhook-test/" not in target_url:
                print(f"   💡 Hint: Production URL requires workflow to be ACTIVE in n8n dashboard")
                print(f"   💡 Make sure workflow 'Master Amazon Social Media Auto-Poster' is toggled ON")
            print(f"   Response: {response.text[:200]}")
            return False
        elif response.status_code == 401 or response.status_code == 403:
            print(f"❌ Authentication failed ({response.status_code})")
            print(f"   Check n8n credentials and permissions")
            return False
        else:
            print(f"❌ Failed to trigger n8n: {response.status_code}")
            print(f"   Response: {response.text[:500]}")
            return False

    except requests.exceptions.Timeout:
        print(f"❌ n8n webhook request timed out (90s)")
        print(f"   The workflow might be processing. Check n8n dashboard for execution status.")
        return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Could not connect to n8n webhook")
        print(f"   URL: {target_url}")
        print(f"   Check if:")
        print(f"   1. n8n instance is running")
        print(f"   2. URL is correct")
        print(f"   3. Internet connection is active")
        return False
    except Exception as e:
        print(f"❌ Error triggering n8n workflow: {e}")
        print(f"   Error type: {type(e).__name__}")
        return False
