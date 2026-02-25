
import sys
import requests
import base64
from config import WP_URL, WP_USERNAME, WP_APP_PASSWORD

def verify_wp_connection():
    print(f"Checking connection to: {WP_URL}")
    print(f"User: {WP_USERNAME}")
    
    if not WP_APP_PASSWORD:
        print("❌ Error: WP_APP_PASSWORD is not set in config.py or .env")
        return False
        
    print(f"Password provided: {'*' * len(WP_APP_PASSWORD)}")

    # Create auth header
    credentials = f"{WP_USERNAME}:{WP_APP_PASSWORD}"
    token = base64.b64encode(credentials.encode()).decode()
    headers = {
        'Authorization': f'Basic {token}',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    # Try to access homepage first to check basic connectivity
    print(f"   Testing homepage reachability: {WP_URL}")
    try:
        home_response = requests.get(WP_URL, headers={'User-Agent': headers['User-Agent']}, timeout=10, verify=False)
        print(f"   Homepage Status: {home_response.status_code}")
    except Exception as e:
        print(f"   Homepage Reachability Failed: {e}")

    # Try to access current user info
    api_url = f"{WP_URL.rstrip('/')}/wp-json/wp/v2/users/me"
    print(f"   Testing API endpoint: {api_url}")
    
    try:
        # Disable SSL verify for testing (in case of cert issues)
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        response = requests.get(api_url, headers=headers, timeout=15, verify=False)
        
        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ Connection Successful!")
            print(f"   Logged in as: {user_data.get('name')} (ID: {user_data.get('id')})")
            return True
        elif response.status_code == 401:
            print(f"❌ Authentication Failed (401)")
            print(f"   Reason: Invalid Username or Application Password")
            print(f"   Check your .env file for typos.")
        elif response.status_code == 403:
            print(f"❌ Access Forbidden (403)")
            print(f"   This often means a security plugin (Wordfence, iThemes) is blocking Python requests.")
            print(f"   Response Body: {response.text[:200]}")
        elif response.status_code == 404:
            print(f"❌ API Endpoint Not Found (404)")
            print(f"   Reason: WordPress REST API might be disabled or URL structure is different.")
            print(f"   Check Permalinks setting in WP Admin (set to 'Post Name').")
        else:
            print(f"❌ Connection Failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Connection Error (Detailed): {e}")
        
    return False

if __name__ == "__main__":
    verify_wp_connection()
