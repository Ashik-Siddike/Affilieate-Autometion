"""
flow_generator.py
=================
Automates image generation on Google Flow (labs.google/fx/tools/flow)
using Playwright browser automation and pre-saved session cookies.
Utilizes verified selectors and headed mode to bypass automation detection.
Supports custom aspect ratios and reference image inputs.
Forces 1x resolution generation to save credits and prevent duplicate generations.
"""

import os
import sys
import json
import time
import base64
from playwright.sync_api import sync_playwright
from PIL import Image

def sanitize_cookies(raw_cookies: list) -> list:
    """Sanitizes cookie definitions to be fully compatible with Playwright."""
    clean_cookies = []
    for c in raw_cookies:
        clean = {
            "name": c["name"],
            "value": c["value"],
            "domain": c["domain"],
            "path": c.get("path", "/"),
            "secure": c.get("secure", True),
            "httpOnly": c.get("httpOnly", True)
        }
        same_site = c.get("sameSite", "Lax")
        if same_site and same_site.lower() in ["lax", "strict", "none"]:
            clean["sameSite"] = same_site.capitalize()
        else:
            clean["sameSite"] = "Lax"
        clean_cookies.append(clean)
    return clean_cookies

# Target resolutions for each aspect ratio (width, height)
ASPECT_RATIO_DIMENSIONS = {
    "16:9": (1376, 774),
    "4:3":  (1032, 774),
    "1:1":  (774, 774),
    "3:4":  (774, 1032),
    "9:16": (774, 1376),
}

def enforce_aspect_ratio(image_path: str, target_ratio: str):
    """Post-process a saved image to ensure it matches the target aspect ratio.
    Uses center-crop to adapt the image without distortion."""
    if target_ratio not in ASPECT_RATIO_DIMENSIONS:
        print(f"[FLOW-GENERATOR] Unknown ratio '{target_ratio}', skipping post-process.")
        return
        
    img = Image.open(image_path)
    w, h = img.size
    target_w, target_h = ASPECT_RATIO_DIMENSIONS[target_ratio]
    target_aspect = target_w / target_h
    current_aspect = w / h
    
    # Check if already close enough (within 5% tolerance)
    if abs(current_aspect - target_aspect) / target_aspect < 0.05:
        print(f"[FLOW-GENERATOR] Image already matches {target_ratio} ratio ({w}x{h}). No crop needed.")
        return
    
    print(f"[FLOW-GENERATOR] Enforcing {target_ratio} ratio: {w}x{h} -> target aspect {target_w}:{target_h}")
    
    # Calculate center-crop box
    if current_aspect > target_aspect:
        # Image is too wide, crop width
        new_w = int(h * target_aspect)
        new_h = h
        left = (w - new_w) // 2
        top = 0
    else:
        # Image is too tall, crop height
        new_w = w
        new_h = int(w / target_aspect)
        left = 0
        top = (h - new_h) // 2
    
    box = (left, top, left + new_w, top + new_h)
    cropped = img.crop(box)
    
    # Resize to exact target dimensions
    resized = cropped.resize((target_w, target_h), Image.LANCZOS)
    resized.save(image_path, "PNG")
    print(f"[FLOW-GENERATOR] Image post-processed to {target_w}x{target_h} ({target_ratio}).")

def generate_google_flow_image(prompt_text: str, output_path: str, aspect_ratio: str = "16:9", reference_image_path: str = None) -> str:
    """
    Launches Playwright Chromium to automate Google Flow image generation.
    Supports aspect ratios: '16:9', '4:3', '1:1', '3:4', '9:16'.
    Forces 1x resolution to prevent multi-image duplicate generations.
    Supports reference image upload to enable image-to-image variant generation.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    cookies_file = os.path.join(base_dir, "cookies.json")
    
    if not os.path.exists(cookies_file):
        raise FileNotFoundError(f"Google Flow session cookies not found at: {cookies_file}. Please export cookies.json first.")
        
    with open(cookies_file, "r") as f:
        raw_cookies = json.load(f)
        
    clean_cookies = sanitize_cookies(raw_cookies)
    
    print(f"[FLOW-GENERATOR] Launching browser context in headed mode (Ratio: {aspect_ratio}, Ref: {reference_image_path})...")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        
        # Load authenticated session cookies
        context.add_cookies(clean_cookies)
        page = context.new_page()
        
        # Inject script to hide webdriver property
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        # 1. Navigate to Google Flow Home
        print("[FLOW-GENERATOR] Navigating to Google Flow...")
        page.goto("https://labs.google/fx/tools/flow")
        
        # 2. Click "+ New project"
        print("[FLOW-GENERATOR] Creating new project...")
        new_project_selector = 'button:has-text("New project")'
        page.wait_for_selector(new_project_selector, timeout=30000)
        page.click(new_project_selector)
        
        # 3. Wait for the project editor URL to load
        print("[FLOW-GENERATOR] Waiting for project editor...")
        page.wait_for_url("**/project/**", timeout=30000)
        
        # 4. Wait for Slate Input container paragraph overlay
        editor_selector = '[data-slate-node="element"]'
        page.wait_for_selector(editor_selector, timeout=30000)
        time.sleep(2)
        
        # 5. Handle Settings Popover Configuration (Aspect Ratio & 1x Resolution)
        try:
            print(f"[FLOW-GENERATOR] Opening settings popup panel...")
            # Locate settings badge (shows Model name e.g. Banana, and Scale/Resolution e.g. 1x)
            settings_badge = page.locator('button:has-text("Banana"), button:has-text("1x"), button:has-text("2x"), button:has-text("3x"), button:has-text("4x")').last
            settings_badge.wait_for(state="visible", timeout=15000)
            settings_badge.click()
            time.sleep(1.5)
            
            # Select Aspect Ratio
            print(f"[FLOW-GENERATOR] Selecting aspect ratio: {aspect_ratio}...")
            ratio_btn = page.locator(f'button.flow_tab_slider_trigger:has-text("{aspect_ratio}")')
            ratio_btn.wait_for(state="visible", timeout=5000)
            ratio_btn.click()
            time.sleep(1)
            
            # Force 1x Resolution to avoid generating multiple duplicate images
            print("[FLOW-GENERATOR] Forcing 1x resolution option...")
            res_btn = page.locator('button.flow_tab_slider_trigger:has-text("1x")')
            res_btn.wait_for(state="visible", timeout=5000)
            res_btn.click()
            time.sleep(1)
            
            # Close the settings popover by pressing the Escape key
            page.keyboard.press("Escape")
            time.sleep(1.5)
            print("[FLOW-GENERATOR] Settings successfully configured (Ratio & 1x Resolution).")
        except Exception as e:
            print(f"[FLOW-GENERATOR] Warning: Failed to change settings ({e}). Defaulting to standard.")
            
        # 6. Handle Reference Image Upload (Image-to-Image / Prompt-Ref)
        if reference_image_path and os.path.exists(reference_image_path):
            print(f"[FLOW-GENERATOR] Uploading reference image from: {reference_image_path}...")
            try:
                # Target the standard hidden file input
                file_input = page.locator('input[type="file"]')
                file_input.wait_for(state="attached", timeout=10000)
                file_input.set_input_files(reference_image_path)
                print("[FLOW-GENERATOR] Reference image uploaded. Waiting for processing...")
                time.sleep(5) # briefly sleep to allow upload flow to trigger
                
                # Check for "Add to Prompt" confirmation button in the asset library overlay
                add_to_prompt_btn = page.locator('button:has-text("Add to Prompt")')
                if add_to_prompt_btn.count() > 0 and add_to_prompt_btn.is_visible():
                    print("[FLOW-GENERATOR] Confirming: clicking 'Add to Prompt' button...")
                    add_to_prompt_btn.click()
                    time.sleep(3)
                
                print("[FLOW-GENERATOR] Reference image attached successfully.")
            except Exception as e:
                print(f"[FLOW-GENERATOR] Error uploading reference image: {e}")
                
        # 7. Focus editor and type the prompt
        print(f"[FLOW-GENERATOR] Entering prompt: '{prompt_text}'")
        page.click(editor_selector)
        time.sleep(1)
        page.keyboard.type(prompt_text)
        time.sleep(2)
        
        # 8. Click generate arrow natively
        print("[FLOW-GENERATOR] Clicking Create...")
        arrow_btn_selector = 'button:has-text("arrow_forward")'
        page.click(arrow_btn_selector)
        
        # 9. Wait for the image generation to complete
        print("[FLOW-GENERATOR] Waiting for image generation (this may take up to 90s)...")
        img_selector = 'img[alt="Generated image"]'
        page.wait_for_selector(img_selector, timeout=120000)
        
        # Wait extra moment for opacity to stabilize to 1.0
        time.sleep(3)
        
        # 10. Retrieve image source URL (relative)
        relative_src = page.get_attribute(img_selector, "src")
        if not relative_src:
            raise ValueError("Failed to retrieve 'src' attribute of the generated image.")
            
        absolute_url = f"https://labs.google{relative_src}"
        print(f"[FLOW-GENERATOR] Image URL: {absolute_url}")
        
        # 11. Download image using browser page context fetch to inherit cookies
        print("[FLOW-GENERATOR] Downloading image data...")
        image_base64 = page.evaluate(f"""async () => {{
            const response = await fetch('{absolute_url}');
            const blob = await response.blob();
            return new Promise((resolve) => {{
                const reader = new FileReader();
                reader.onloadend = () => resolve(reader.result);
                reader.readAsDataURL(blob);
            }});
        }}""")
        
        # Clean base64 header
        if "," in image_base64:
            base64_data = image_base64.split(",")[1]
        else:
            base64_data = image_base64
            
        # Create output directory
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save PNG locally
        with open(output_path, "wb") as f:
            f.write(base64.b64decode(base64_data))
            
        print("[FLOW-GENERATOR] Image saved successfully. Closing browser.")
        browser.close()
        
        # Post-process: Enforce correct aspect ratio via center-crop
        try:
            enforce_aspect_ratio(output_path, aspect_ratio)
        except Exception as crop_err:
            print(f"[FLOW-GENERATOR] Warning: Post-processing crop failed: {crop_err}")
        
        return output_path

if __name__ == "__main__":
    # Test execution
    test_prompt = "A high-quality minimalist vector icon of a mechanical keyboard switch, line art, dark slate aesthetic."
    test_output = "output/test_flow_aspect.png"
    try:
        # Try generating 1:1 image
        generate_google_flow_image(test_prompt, test_output, aspect_ratio="1:1")
        print(f"Success! Test image generated at: {test_output}")
    except Exception as e:
        print(f"Error: {e}")
