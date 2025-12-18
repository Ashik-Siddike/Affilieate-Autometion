import requests
import base64
from config import WP_URL, WP_USERNAME, WP_APP_PASSWORD

def get_auth_header():
    credentials = f"{WP_USERNAME}:{WP_APP_PASSWORD}"
    token = base64.b64encode(credentials.encode())
    return {'Authorization': f'Basic {token.decode("utf-8")}'}

def upload_media(image_url, title=None):
    """
    Downloads image from URL and uploads to WordPress.
    Returns the Media ID.
    """
    try:
        # Download image
        response = requests.get(image_url)
        if response.status_code != 200:
            print(f"Failed to download image from {image_url}")
            return None
        
        filename = image_url.split('/')[-1] or "image.jpg"
        content_type = response.headers.get('content-type', 'image/jpeg')

        # Upload to WordPress
        api_url = f"{WP_URL}/wp-json/wp/v2/media"
        headers = get_auth_header()
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

def publish_post(title, content, category_id=1, image_url=None):
    """
    Creates a new post in WordPress.
    """
    try:
        api_url = f"{WP_URL}/wp-json/wp/v2/posts"
        headers = get_auth_header()
        headers.update({'Content-Type': 'application/json'})
        
        post_data = {
            'title': title,
            'content': content,
            'status': 'publish' # or 'draft'
        }
        
        if image_url:
            print(f"Uploading featured image: {image_url}")
            media_id = upload_media(image_url, title)
            if media_id:
                post_data['featured_media'] = media_id
                
        response = requests.post(api_url, json=post_data, headers=headers)
        
        if response.status_code == 201:
            print(f"Post published successfully: {title}")
            return response.json().get('link')
        else:
            print(f"Failed to create post: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        print(f"Error creating post: {e}")
        return None
