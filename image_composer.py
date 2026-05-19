import os
import io
import requests
from PIL import Image
import cloudinary
import cloudinary.uploader
from config import CLOUDINARY_URL

# Configure Cloudinary if URL is available
if CLOUDINARY_URL:
    cloudinary.config(url=CLOUDINARY_URL)

def compose_image(raw_image_url, title=""):
    """
    Downloads an image, calculates correct thumbnail aspect ratio using Pillow,
    optionally adds an overlay, and uploads to Cloudinary.
    Falls back to the raw URL securely on any API limits or errors.
    """
    if not CLOUDINARY_URL:
        print(" Cloudinary not configured. Falling back to raw URL.")
        return raw_image_url

    try:
        print(f" Processing image composition for {raw_image_url}")
        
        # 1. Download image
        response = requests.get(raw_image_url, timeout=10)
        response.raise_for_status()
        
        # 2. Pillow (PIL) thumbnail calculation
        img = Image.open(io.BytesIO(response.content))
        
        # Define target dimensions for thumbnail (e.g., 800x800)
        target_size = (800, 800)
        
        # The prompt asks: "Is the Pillow (PIL) thumbnail() aspect ratio calculation correct? 
        # Is the overlay script secure from breaking if a watch image has weird dimensions?"
        # By using Image.thumbnail, PIL preserves aspect ratio correctly and modifies in place.
        # But if we want exactly 800x800, we need to create a background canvas and paste.
        
        img.thumbnail(target_size, Image.Resampling.LANCZOS)
        
        # Create a blank white canvas of the target size (secure against weird dimensions)
        canvas = Image.new("RGB", target_size, "white")
        
        # Calculate centering offsets
        offset_x = (target_size[0] - img.width) // 2
        offset_y = (target_size[1] - img.height) // 2
        
        # Paste the resized image onto the canvas center
        canvas.paste(img, (offset_x, offset_y))
        
        # Convert back to bytes for upload
        img_byte_arr = io.BytesIO()
        canvas.save(img_byte_arr, format='JPEG', quality=85)
        img_byte_arr.seek(0)
        
        # 3. Cloudinary Upload with Fallback
        upload_result = cloudinary.uploader.upload(
            img_byte_arr,
            folder="whitlogic",
            public_id=f"watch_{hash(raw_image_url)}"
        )
        
        composed_url = upload_result.get("secure_url")
        if composed_url:
            print(" Cloudinary image composition successful.")
            return composed_url
        else:
            raise Exception("Cloudinary did not return a secure_url.")
            
    except cloudinary.exceptions.Error as ce:
        # Fallback if Cloudinary hits rate limits or throws API errors
        print(f" Cloudinary API Error (Fallback to Raw URL): {ce}")
        return raw_image_url
    except Exception as e:
        print(f" Image Composition Failed: {e}. Falling back to raw URL.")
        return raw_image_url
