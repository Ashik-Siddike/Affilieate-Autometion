import requests
import base64
from config import WP_URL, WP_USERNAME, WP_APP_PASSWORD

def get_auth_header(username=None, password=None):
    # Use provided credentials or fallback to config
    user = username if username else WP_USERNAME
    pwd = password if password else WP_APP_PASSWORD
    
    if not user or not pwd:
        print("❌ Error: Missing WordPress credentials.")
        return None
        
    credentials = f"{user}:{pwd}"
    token = base64.b64encode(credentials.encode())
    return {
        'Authorization': f'Basic {token.decode("utf-8")}',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

def upload_media(image_url, title=None, wp_url=None, wp_username=None, wp_password=None):
    """
    Downloads image from URL and uploads to WordPress.
    Returns the Media ID.
    """
    target_url = wp_url if wp_url else WP_URL
    
    try:
        # Download image
        response = requests.get(image_url)
        if response.status_code != 200:
            print(f"Failed to download image from {image_url}")
            return None
        
        filename = image_url.split('/')[-1] or "image.jpg"
        content_type = response.headers.get('content-type', 'image/jpeg')

        # Upload to WordPress
        api_url = f"{target_url}/wp-json/wp/v2/media"
        headers = get_auth_header(wp_username, wp_password)
        if not headers:
            return None
            
        headers.update({
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Type": content_type
        })
        
        wp_response = requests.post(api_url, data=response.content, headers=headers)
        
        if wp_response.status_code == 201:
            return wp_response.json().get('id')
        else:
            print(f"WP Upload Failed: {wp_response.status_code} - {wp_response.text}")
            return None

    except Exception as e:
        print(f"Error uploading image: {e}")
        return None

def publish_post(title, content, category_id=1, image_url=None, wp_url=None, wp_username=None, wp_password=None, status="publish", publish_date=None):
    """
    Creates a new post in WordPress.
    """
    target_url = wp_url if wp_url else WP_URL
    
    try:
        api_url = f"{target_url}/wp-json/wp/v2/posts"
        headers = get_auth_header(wp_username, wp_password)
        if not headers:
            return None
            
        headers.update({'Content-Type': 'application/json'})
        
        post_data = {
            'title': title,
            'content': content,
            'status': status
        }
        
        if publish_date:
            post_data['date'] = publish_date
            post_data['status'] = 'future'

        if image_url:
            print(f"Uploading featured image: {image_url}")
            media_id = upload_media(image_url, title, target_url, wp_username, wp_password)
            if media_id:
                post_data['featured_media'] = media_id
                
        response = requests.post(api_url, json=post_data, headers=headers)
        
        if response.status_code == 201:
            print(f"Post published/scheduled successfully: {title}")
            return response.json().get('link')
        else:
            print(f"Failed to create post: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        print(f"Error creating post: {e}")
        return None
