"""
main.py
=======
The primary orchestrator script for the Standalone Social Media Growing Agent.
1. Loads settings from its local `.env`.
2. Reads, rotates, and tracks the current topic from `topics.txt`.
3. Invokes Gemini API (with key rotation and anti-AI tone constraints) to get copywriting.
4. Calls `card_generator.py` to compile a beautiful PNG image card.
5. Uploads the PNG to Cloudinary (if configured) to get a public URL.
6. Sends the payload to Make.com and/or n8n webhooks for distribution.
7. Saves history logs locally.
"""

import os
import sys
import json
import time
import requests
from datetime import datetime
from dotenv import load_dotenv

# Ensure local imports work correctly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from card_generator import generate_card

# 1. Load local environment configurations
LOCAL_ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(LOCAL_ENV_PATH):
    print(f"[GROWING-AGENT] Loading env from: {LOCAL_ENV_PATH}")
    load_dotenv(LOCAL_ENV_PATH, override=True)
else:
    print("[GROWING-AGENT] Warning: Local .env file not found. Falling back to system environment variables.")
    load_dotenv() # fallback to root .env if active in path

# Configuration Settings
MAKE_WEBHOOK_URL = os.getenv("MAKE_WEBHOOK_URL", "")
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "")
BRAND_NAME = os.getenv("BRAND_NAME", "Whitlogic")
CLOUDINARY_URL = os.getenv("CLOUDINARY_URL", "")

# Load Gemini API Keys
_raw_keys = os.getenv("GEMINI_API_KEYS", "")
GEMINI_API_KEYS = [k.strip() for k in _raw_keys.replace("\n", ",").split(",") if k.strip()]

# Active Key Rotation Trackers
_current_key_idx = 0

def get_current_api_key():
    if not GEMINI_API_KEYS:
        raise ValueError("No GEMINI_API_KEYS defined in env variables.")
    return GEMINI_API_KEYS[_current_key_idx]

def rotate_api_key():
    global _current_key_idx
    if len(GEMINI_API_KEYS) > 1:
        _current_key_idx = (_current_key_idx + 1) % len(GEMINI_API_KEYS)
        print(f"[GROWING-AGENT] API Key rotated to key {_current_key_idx + 1}/{len(GEMINI_API_KEYS)}")
    else:
        print("[GROWING-AGENT] Only 1 key available. Cannot rotate.")

def is_quota_limit_error(error_msg):
    err = str(error_msg).lower()
    return any(indicator in err for indicator in ["429", "quota", "limit", "exhausted", "credit"])

# 2. Topic Rotation System
def get_next_topic():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    topics_file = os.path.join(base_dir, "topics.txt")
    state_file = os.path.join(base_dir, "post_state.json")
    
    if not os.path.exists(topics_file):
        raise FileNotFoundError(f"Topics configuration file '{topics_file}' does not exist.")
        
    with open(topics_file, "r", encoding="utf-8") as f:
        topics = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]
        
    if not topics:
        raise ValueError(f"Topics file '{topics_file}' is empty.")
        
    # Read rotation state
    last_index = -1
    first_run_date = None
    if os.path.exists(state_file):
        try:
            with open(state_file, "r") as sf:
                state = json.load(sf)
                last_index = state.get("last_index", -1)
                first_run_date = state.get("first_run_date")
        except Exception:
            pass

    if not first_run_date:
        first_run_date = datetime.now().isoformat()
        days_active = 0
    else:
        try:
            first_run = datetime.fromisoformat(first_run_date)
            days_active = (datetime.now() - first_run).days
        except Exception:
            days_active = 0

    print(f"[GROWING-AGENT] Bot active for {days_active} days (Phase 1 limit: 30 days).")
    
    if days_active >= 30:
        print("[GROWING-AGENT] Phase 2: Active days >= 30. Triggering Twitter tracker to pull fresh trends...")
        try:
            from twitter_tracker import update_topics_pool
            update_topics_pool()
        except Exception as te:
            print(f"[GROWING-AGENT] Warning: Twitter trend update failed: {te}")
            
    # Reload topics in case twitter tracker updated the file
    with open(topics_file, "r", encoding="utf-8") as f:
        topics = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]

    if not topics:
        raise ValueError(f"Topics file '{topics_file}' is empty.")

    # Calculate next index
    next_index = (last_index + 1) % len(topics)
    selected_topic = topics[next_index]
    
    # Save rotation state
    try:
        with open(state_file, "w") as sf:
            json.dump({
                "last_index": next_index, 
                "last_topic": selected_topic,
                "first_run_date": first_run_date
            }, sf, indent=2)
    except Exception as e:
        print(f"[GROWING-AGENT] Error saving state file: {e}")
        
    print(f"[GROWING-AGENT] Selected Topic #{next_index + 1}: '{selected_topic}'")
    return selected_topic

# 3. Gemini Copywriting Engine
SYSTEM_PROMPT = """
You are an expert social media copywriter specializing in tech productivity, mechanical keyboards, office ergonomics, and smart home setups.
Your goal is to write highly engaging, human-sounding social media content for a tech account.
The content MUST be purely educational, informative, or trivia-based. NO promotional content, NO affiliate links, and NO sales pitches. We are in the profile-warming phase to gain followers.

Anti-AI Tone Rules:
1. Write like a real tech enthusiast who is sharing a tip on Reddit or Twitter.
2. Absolutely DO NOT use any of these forbidden words or phrases:
   - unleash, unlock, realm, landscape, tapestry, symphony, game-changer
   - delve, dive deep, bustling, vibrant, meticulous, paramount, elevate
   - testament, not only, in conclusion, last but not least, when it comes to
   - it is important to remember, ultimately, furthermore, moreover, additionally
   - consequently, therefore, thus, hence, nonetheless, nevertheless, look no further
3. Keep paragraphs short (1-3 sentences maximum).
4. Vary sentence length (use some very short sentences of 3-5 words, and some medium sentences. Avoid long, run-on sentences).
5. Start or end the post with a natural question that encourages comments (e.g., "What switch type is on your desk right now?").

You must respond with a raw JSON object containing exactly these keys:
{
  "category_tag": "A punchy 2-3 word category name in all caps (e.g., WORKSPACE HACK, KEYBOARD GUIDE)",
  "card_text": "A short, punchy 1-2 sentence tip/fact (under 120 characters) suitable for placing on an image card. Be direct and clear.",
  "fb_content": "A detailed, engaging post for Facebook/LinkedIn. Use line breaks, bullet points, and 2-3 relevant emojis/hashtags naturally. Avoid emoji spam.",
  "ig_content": "A visually engaging post for Instagram/Pinterest. Similar to fb_content but slightly shorter, focusing on visual cues. Add hashtags at the very end.",
  "x_content": "A single, highly punchy tweet (under 280 characters including spaces and 1-2 hashtags) that gets straight to the point."
}

Ensure the output is valid JSON and nothing else. Return ONLY the JSON object. Do not wrap the JSON in Markdown tags.
"""

def generate_social_bundle(topic):
    from google import genai
    from google.genai import errors
    
    prompt = f"Generate a social media engagement bundle for the topic: '{topic}'"
    
    preferred_models = ['gemini-2.5-flash', 'gemini-1.5-flash']
    max_retries = len(GEMINI_API_KEYS) * 2
    
    for attempt in range(max_retries):
        api_key = get_current_api_key()
        client = genai.Client(api_key=api_key)
        
        for model in preferred_models:
            try:
                print(f"[GROWING-AGENT] Requesting content from model: {model} using key #{_current_key_idx + 1}...")
                response = client.models.generate_content(
                    model=model,
                    contents=SYSTEM_PROMPT + "\n\n" + prompt
                )
                
                if response and response.text:
                    raw_text = response.text.strip()
                    
                    # Clean up json markdown fences if Gemini added them
                    if raw_text.startswith("```json"):
                        raw_text = raw_text.replace("```json", "", 1)
                    if raw_text.endswith("```"):
                        raw_text = raw_text[:-3].strip()
                    raw_text = raw_text.strip()
                    
                    # Try parsing as JSON
                    try:
                        social_data = json.loads(raw_text)
                        
                        # Validate required keys
                        required = ["category_tag", "card_text", "fb_content", "ig_content", "x_content"]
                        missing = [k for k in required if k not in social_data]
                        if missing:
                            print(f"[GROWING-AGENT] Warning: Model returned JSON with missing keys: {missing}. Retrying...")
                            continue
                            
                        # Fluff check
                        FLUFF_WORDS = ["unleash", "unlock", "realm", "landscape", "tapestry", "delve", "dive deep", "elevate"]
                        found_fluff = [w for w in FLUFF_WORDS if w in raw_text.lower()]
                        if found_fluff:
                            print(f"[GROWING-AGENT] Fluff detected in AI output: {found_fluff}. Retrying request...")
                            continue
                            
                        print(f"[GROWING-AGENT] Content generated successfully and passed validation.")
                        return social_data
                        
                    except json.JSONDecodeError:
                        print("[GROWING-AGENT] Error: Response was not valid JSON. Content was:")
                        print(raw_text[:300])
                        print("[GROWING-AGENT] Retrying...")
                        continue
                        
            except errors.APIError as api_err:
                if is_quota_limit_error(api_err):
                    print(f"[GROWING-AGENT] Quota/API limit hit: {api_err}")
                    rotate_api_key()
                    break # break inner model loop, proceed to next key in outer loop
                else:
                    print(f"[GROWING-AGENT] API Error: {api_err}")
            except Exception as e:
                print(f"[GROWING-AGENT] Unexpected model error: {e}")
                
    raise RuntimeError("Failed to generate valid social media bundle after running out of keys/models.")

# 4. Cloudinary Image Uploader (Optional)
def upload_image_to_cloudinary(file_path):
    if not CLOUDINARY_URL:
        print("[GROWING-AGENT] CLOUDINARY_URL is not set. Skipping Cloudinary upload.")
        return ""
        
    try:
        import cloudinary
        import cloudinary.uploader
        
        cloudinary.config(url=CLOUDINARY_URL)
        print(f"[GROWING-AGENT] Uploading image '{file_path}' to Cloudinary...")
        res = cloudinary.uploader.upload(file_path, folder="growing_agent_cards")
        secure_url = res.get("secure_url", "")
        print(f"[GROWING-AGENT] Upload success! CDN URL: {secure_url}")
        return secure_url
    except ImportError:
        print("[GROWING-AGENT] Warning: 'cloudinary' library not installed. Install using requirements.txt.")
        return ""
    except Exception as e:
        print(f"[GROWING-AGENT] Cloudinary upload failed: {e}")
        return ""

# 5. Webhook Dispatches
def dispatch_webhooks(payload):
    success = False
    
    # ── Make.com Webhook ──
    if MAKE_WEBHOOK_URL:
        try:
            print(f"[GROWING-AGENT] Dispatching to Make Webhook: {MAKE_WEBHOOK_URL}")
            res = requests.post(MAKE_WEBHOOK_URL, json=payload, headers={"Content-Type": "application/json"}, timeout=30)
            if res.status_code == 200:
                print("[GROWING-AGENT] Make Webhook succeeded!")
                success = True
            else:
                print(f"[GROWING-AGENT] Make Webhook failed with status: {res.status_code}. Response: {res.text}")
        except Exception as e:
            print(f"[GROWING-AGENT] Error sending to Make Webhook: {e}")
            
    # ── n8n Webhook ──
    if N8N_WEBHOOK_URL:
        try:
            print(f"[GROWING-AGENT] Dispatching to n8n Webhook: {N8N_WEBHOOK_URL}")
            # Standardize n8n expected payload (similar to root trigger_n8n_workflow keys)
            n8n_payload = {
                "title": payload["category"],
                "description": payload["card_text"],
                "amazon_link": "N/A - Growth Post",
                "image_url": payload["image_url"],
                "social_caption": payload["facebook_caption"],
                "category": payload["category"],
                "long_description": payload["facebook_caption"],
                "tweet": payload["twitter_caption"],
                "pinterest_title": payload["category"],
                "pinterest_desc": payload["instagram_caption"],
                "linkedin": payload["facebook_caption"]
            }
            res = requests.post(N8N_WEBHOOK_URL, json=n8n_payload, headers={"Content-Type": "application/json"}, timeout=30)
            if res.status_code == 200:
                print("[GROWING-AGENT] n8n Webhook succeeded!")
                success = True
            else:
                print(f"[GROWING-AGENT] n8n Webhook failed with status: {res.status_code}. Response: {res.text}")
        except Exception as e:
            print(f"[GROWING-AGENT] Error sending to n8n Webhook: {e}")
            
    if not MAKE_WEBHOOK_URL and not N8N_WEBHOOK_URL:
        print("[GROWING-AGENT] Warning: No MAKE_WEBHOOK_URL or N8N_WEBHOOK_URL defined. Webhook dispatch skipped.")
        
    return success

# 6. Core Orchestration Run
def run_cycle():
    print("==================================================")
    print(f"Starting Growing Agent Cycle: {datetime.now().isoformat()}")
    print("==================================================")
    
    # Create output directory
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Get next topic
    topic = get_next_topic()
    
    # 2. Generate Copywriting Bundle
    bundle = generate_social_bundle(topic)
    
    # 3. Create Custom Visual Image Card (Try Google Flow first, fallback to Pillow card generator)
    timestamp = int(time.time())
    img_filename = f"post_{timestamp}.png"
    local_img_path = os.path.join(output_dir, img_filename)
    
    flow_success = False
    try:
        from flow_generator import generate_google_flow_image
        print(f"[GROWING-AGENT] Attempting Google Flow image generation for prompt: '{bundle['card_text']}'")
        generate_google_flow_image(bundle["card_text"], local_img_path)
        print(f"[GROWING-AGENT] Google Flow image successfully generated and saved to: {local_img_path}")
        flow_success = True
    except Exception as fe:
        print(f"[GROWING-AGENT] Warning: Google Flow generation failed ({fe}). Falling back to Pillow card generator...")
        
    if not flow_success:
        print(f"[GROWING-AGENT] Generating Pillow visual card for: '{bundle['card_text']}'")
        generate_card(
            text=bundle["card_text"],
            category_tag=bundle["category_tag"],
            brand_name=BRAND_NAME,
            output_path=local_img_path
        )
        print(f"[GROWING-AGENT] Pillow graphic card saved to: {local_img_path}")
    
    # 4. Upload Image to Cloudinary if URL exists
    cdn_url = upload_image_to_cloudinary(local_img_path)
    
    # 5. Compile payload
    payload = {
        "category": bundle["category_tag"],
        "card_text": bundle["card_text"],
        "facebook_caption": bundle["fb_content"],
        "instagram_caption": bundle["ig_content"],
        "twitter_caption": bundle["x_content"],
        "image_url": cdn_url,
        "local_image_path": local_img_path,
        "timestamp": timestamp
    }
    
    # 6. Dispatch to webhook
    webhook_status = dispatch_webhooks(payload)
    
    # 7. Log post audit trail locally
    history_file = os.path.join(output_dir, "post_history.jsonl")
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "topic": topic,
        "payload": payload,
        "webhook_dispatched": webhook_status
    }
    try:
        with open(history_file, "a", encoding="utf-8") as hf:
            hf.write(json.dumps(log_entry) + "\n")
        print(f"[GROWING-AGENT] Cycle complete. History logged to: {history_file}")
    except Exception as e:
        print(f"[GROWING-AGENT] Failed to write history log: {e}")
        
    print("==================================================")
    print("Growing Agent Cycle Completed Successfully!")
    print("==================================================")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Standalone Social Media Growing Agent")
    parser.add_argument("--loop", action="store_true", help="Run the agent in a continuous daemon loop")
    args = parser.parse_args()
    
    if args.loop:
        interval_hours = int(os.getenv("POST_INTERVAL_HOURS", "6"))
        interval_seconds = interval_hours * 3600
        print(f"[GROWING-AGENT] Running in loop daemon mode. Interval: {interval_hours} hours ({interval_seconds} seconds).")
        while True:
            try:
                run_cycle()
            except Exception as e:
                print(f"[GROWING-AGENT] Cycle error in daemon mode: {e}")
            
            print(f"[GROWING-AGENT] Sleeping for {interval_hours} hours... Press Ctrl+C to terminate.")
            slept = 0
            while slept < interval_seconds:
                time.sleep(10)
                slept += 10
    else:
        try:
            run_cycle()
        except Exception as err:
            print(f"[GROWING-AGENT] Critical Cycle Failure: {err}")
            sys.exit(1)
