"""
flow_generator.py
=================
Automates image generation on Google Flow (labs.google/fx/tools/flow)
using Playwright browser automation and pre-saved session cookies.
Utilizes verified selectors and headed mode to bypass automation detection.
"""

import os
import sys
import json
import time
import base64
from playwright.sync_api import sync_playwright

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

def generate_google_flow_image(prompt_text: str, output_path: str) -> str:
    """
    Launches Playwright Chromium to automate Google Flow image generation.
    Bypasses security checks by running headed (headless=False) and spoofing webdriver.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    cookies_file = os.path.join(base_dir, "cookies.json")
    
    if not os.path.exists(cookies_file):
        raise FileNotFoundError(f"Google Flow session cookies not found at: {cookies_file}. Please export cookies.json first.")
        
    with open(cookies_file, "r") as f:
        raw_cookies = json.load(f)
        
    clean_cookies = sanitize_cookies(raw_cookies)
    
    print("[FLOW-GENERATOR] Launching browser context in headed mode...")
    with sync_playwright() as p:
        # Launch headed to bypass fingerprint and bot checks
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
        page.goto("https://labs.google/fx/tools/flow", wait_until="networkidle")
        
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
        
        # 5. Focus editor and type the prompt
        print(f"[FLOW-GENERATOR] Entering prompt: '{prompt_text}'")
        page.click(editor_selector)
        time.sleep(1)
        page.keyboard.type(prompt_text)
        time.sleep(2)
        
        # 6. Click generate arrow natively
        print("[FLOW-GENERATOR] Clicking Create...")
        arrow_btn_selector = 'button:has-text("arrow_forward")'
        page.click(arrow_btn_selector)
        
        # 7. Wait for the image generation to complete
        print("[FLOW-GENERATOR] Waiting for image generation (this may take up to 90s)...")
        img_selector = 'img[alt="Generated image"]'
        page.wait_for_selector(img_selector, timeout=120000)
        
        # Wait extra moment for opacity to stabilize to 1.0
        time.sleep(3)
        
        # 8. Retrieve image source URL (relative)
        relative_src = page.get_attribute(img_selector, "src")
        if not relative_src:
            raise ValueError("Failed to retrieve 'src' attribute of the generated image.")
            
        absolute_url = f"https://labs.google{relative_src}"
        print(f"[FLOW-GENERATOR] Image URL: {absolute_url}")
        
        # 9. Download image using browser page context fetch to inherit cookies
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
        return output_path

if __name__ == "__main__":
    # Test execution
    test_prompt = "A high-quality minimalist vector icon of a mechanical keyboard switch, line art, dark slate aesthetic."
    test_output = "output/test_flow_generated.png"
    try:
        generate_google_flow_image(test_prompt, test_output)
        print(f"Success! Test image generated at: {test_output}")
    except Exception as e:
        print(f"Error: {e}")
