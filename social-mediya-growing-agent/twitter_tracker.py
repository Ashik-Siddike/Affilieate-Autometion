"""
twitter_tracker.py
==================
Scrapes recent tweets from a curated list of tech influencers using Nitter RSS feeds.
Passes raw tweets to Gemini to extract high-quality, niche-relevant topics and appends
them to topics.txt (while ensuring no duplicates).
Saves media image attachments locally and maps them to topics in topics_metadata.json.
"""

import os
import re
import json
import time
import random
import requests
import xml.etree.ElementTree as ET
from dotenv import load_dotenv

# Load configurations
LOCAL_ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(LOCAL_ENV_PATH, override=True)

# List of backup public Nitter instances to ensure uptime
NITTER_INSTANCES = [
    "https://nitter.net",
    "https://nitter.cz",
    "https://nitter.privacydev.net",
    "https://nitter.poast.org",
    "https://nitter.it",
    "https://nitter.unixfox.eu"
]

# Influencers curated list from user
INFLUENCERS = [
    "TheNextWeb", "recode", "ZDNet", "TechCrunch", "TechRepublic", "techbusiness",
    "Engadget", "Gigaom", "WIRED", "weusegadgets", "arstechnica", "SmartPlanet",
    "alexia", "parislemon", "neilpatel", "hamids", "jasonfried", "unclebobmartin",
    "rabois", "hadip", "Jessicalessin", "nzkoz", "AmyStephen", "alexwilliams",
    "ZDNetCharlie", "acoolong", "KentBeck", "LeoLaporte", "peeplaja", "mssonicflare",
    "scottbelsky", "martinfowler", "jank0", "Paul_Clifford", "codinghorror",
    "Pilchie", "defunkt", "Jeresig", "retomeier", "avdi", "MrAlanCooper",
    "SaraJChipps", "davidfowl", "WardCunningham", "mikewcohn", "OdeToCode",
    "sarahmei", "cdibona", "lifo", "hone02"
]

# Target niches we grow:
NICHES_DESCRIPTION = """
- Mechanical keyboards, keycaps, switches, custom build guides.
- Office ergonomics, standing desks, monitor arms, wrist pain relief, healthy workspaces.
- Developer/Designer workspace productivity, setups, light bars, multi-monitor productivity.
- Smart home office automation, security cameras, plugs, remote worker setup tips.
"""

def fetch_tweets_for_user(username: str) -> list[dict]:
    """Fetches the latest 3 tweets from a user's Nitter RSS feed, trying different instances."""
    tweets = []
    
    # Shuffle instances to distribute load
    instances = NITTER_INSTANCES.copy()
    random.shuffle(instances)
    
    for instance in instances:
        url = f"{instance}/{username}/rss"
        try:
            # Add user agent to prevent blocks
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200 and response.text:
                # Parse RSS XML
                root = ET.fromstring(response.content)
                items = root.findall(".//item")
                
                for item in items[:3]: # grab latest 3 tweets
                    title = item.find("title")
                    desc = item.find("description")
                    
                    raw_desc = desc.text if desc is not None and desc.text else ""
                    tweet_text = raw_desc
                    if not tweet_text and title is not None:
                        tweet_text = title.text
                        
                    # Extract image URL before stripping HTML tags
                    img_url = None
                    img_matches = re.findall(r'<img\s+[^>]*src=["\']([^"\']+)["\']', raw_desc)
                    if img_matches:
                        img_url = img_matches[0]
                        # Convert relative paths to absolute using the current nitter instance URL
                        if img_url.startswith("/"):
                            img_url = f"{instance}{img_url}"
                            
                    # Clean up HTML tags
                    tweet_text = re.sub(r'<[^>]+>', ' ', tweet_text)
                    tweet_text = ' '.join(tweet_text.split())
                    
                    # Ignore retweets or empty content
                    if tweet_text and not tweet_text.startswith("RT @"):
                        tweets.append({
                            "text": tweet_text[:300],
                            "image_url": img_url
                        })
                        
                if tweets:
                    print(f"[TWITTER-TRACKER] Successfully fetched {len(tweets)} tweets for @{username} via {instance}")
                    return tweets
        except Exception:
            # Continue trying next Nitter instance on failure
            continue
            
    print(f"[TWITTER-TRACKER] Failed to fetch tweets for @{username} from all instances.")
    return []

def extract_topics_via_gemini(tweets: list[dict]) -> list[dict]:
    """Uses Gemini to filter and convert raw tweets into high-quality educational topics with index mapping."""
    from google import genai
    
    _raw_keys = os.getenv("GEMINI_API_KEYS", "")
    api_keys = [k.strip() for k in _raw_keys.replace("\n", ",").split(",") if k.strip()]
    if not api_keys:
        print("[TWITTER-TRACKER] Warning: No GEMINI_API_KEYS found. Cannot extract topics.")
        return []
        
    client = genai.Client(api_key=api_keys[0])
    
    # Format tweets as a numbered block
    tweets_list = []
    for idx, t in enumerate(tweets):
        tweets_list.append(f"[{idx}] {t['text']}")
    tweets_block = "\n---\n".join(tweets_list)
    
    system_prompt = f"""
You are an expert tech researcher and content curator.
Your task is to analyze recent tweets from tech industry leaders and extract evergreen, highly engaging educational/informational topics matching these niches:
{NICHES_DESCRIPTION}

Rules:
1. Ignore tweets about personal stuff, conferences, self-promotions, political views, random complaints, or irrelevant niches.
2. Formulate each relevant tweet insight into a clean, standalone topic question or statement (max 10 words), similar to:
   - "How to position dual monitors to minimize neck strain"
   - "Why mechanical keyboard stabilizers make a huge sound difference"
3. Do not use AI fluff words (unleash, elevate, dive deep, realm, tapestry).
4. Output a raw JSON list of objects, where each object has:
   - "topic": The clean extracted topic string.
   - "tweet_index": The 0-based integer index of the tweet this topic was extracted from.
   
   Example output format:
   [
     {{"topic": "Why mechanical keyboard stabilizers make a huge sound difference", "tweet_index": 2}}
   ]
"""
    
    prompt = f"Extract niche-relevant educational topics from these numbered tweets:\n\n{tweets_block}"
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=system_prompt + "\n\n" + prompt
        )
        if response and response.text:
            text = response.text.strip()
            # Strip markdown fences if added
            if text.startswith("```json"):
                text = text.replace("```json", "", 1)
            if text.endswith("```"):
                text = text[:-3].strip()
            text = text.strip()
            
            topics_data = json.loads(text)
            if isinstance(topics_data, list):
                valid_topics = []
                for entry in topics_data:
                    if isinstance(entry, dict) and "topic" in entry and "tweet_index" in entry:
                        valid_topics.append({
                            "topic": entry["topic"].strip(),
                            "tweet_index": int(entry["tweet_index"])
                        })
                return valid_topics
    except Exception as e:
        print(f"[TWITTER-TRACKER] Gemini extraction failed: {e}")
        
    return []

def get_existing_topics(topics_path: str) -> list[str]:
    """Reads all current topics from topics.txt."""
    if not os.path.exists(topics_path):
        return []
    with open(topics_path, "r", encoding="utf-8") as f:
        return [line.strip().lower() for line in f if line.strip() and not line.strip().startswith("#")]

def download_image(url: str, save_path: str) -> bool:
    """Downloads an image from URL and saves it locally."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code == 200:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, "wb") as f:
                f.write(res.content)
            return True
    except Exception as e:
        print(f"[TWITTER-TRACKER] Failed to download image {url}: {e}")
    return False

def update_topics_pool():
    """Selects random influencers, crawls their feeds, extracts new topics, downloads media, and updates topics.txt."""
    print("[TWITTER-TRACKER] Starting trend-sourcing update...")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    topics_path = os.path.join(base_dir, "topics.txt")
    metadata_path = os.path.join(base_dir, "topics_metadata.json")
    output_dir = os.path.join(base_dir, "output")
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Randomly pick 5 influencers to crawl this cycle to bypass rate limits and keep it fast
    selected_users = random.sample(INFLUENCERS, min(len(INFLUENCERS), 5))
    print(f"[TWITTER-TRACKER] Curating feeds from: {selected_users}")
    
    all_tweets = []
    for user in selected_users:
        tweets = fetch_tweets_for_user(user)
        all_tweets.extend(tweets)
        time.sleep(1) # brief rate limiting sleep
        
    if not all_tweets:
        print("[TWITTER-TRACKER] No tweets fetched in this cycle. Skipping update.")
        return
        
    # 2. Extract topics via Gemini
    new_topics_data = extract_topics_via_gemini(all_tweets)
    if not new_topics_data:
        print("[TWITTER-TRACKER] No new topics extracted by Gemini.")
        return
        
    # 3. Load existing topics for duplicate check
    existing_normalized = get_existing_topics(topics_path)
    
    # Load metadata file if it exists
    metadata = {}
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, "r", encoding="utf-8") as mf:
                metadata = json.load(mf)
        except Exception:
            pass
            
    # 4. Append only unique topics and handle their images
    appended_count = 0
    try:
        with open(topics_path, "a", encoding="utf-8") as f:
            for entry in new_topics_data:
                topic = entry["topic"]
                t_idx = entry["tweet_index"]
                
                # Boundary check for index
                if t_idx < 0 or t_idx >= len(all_tweets):
                    continue
                    
                orig_tweet = all_tweets[t_idx]
                
                # Basic duplicate check: clean string and check containment
                clean_topic = re.sub(r'[^\w\s]', '', topic.strip().lower())
                is_duplicate = False
                for exist in existing_normalized:
                    clean_exist = re.sub(r'[^\w\s]', '', exist)
                    # If 80% similar or subset
                    if clean_topic in clean_exist or clean_exist in clean_topic:
                        is_duplicate = True
                        break
                        
                if not is_duplicate:
                    f.write(topic.strip() + "\n")
                    print(f"[TWITTER-TRACKER] Appended new topic: '{topic.strip()}'")
                    
                    # Handle image download if available
                    img_url = orig_tweet.get("image_url")
                    local_img_path = None
                    if img_url:
                        timestamp = int(time.time())
                        filename = f"scraped_ref_{timestamp}_{random.randint(100, 999)}.jpg"
                        save_path = os.path.join(output_dir, filename)
                        print(f"[TWITTER-TRACKER] Downloading tweet image: {img_url}")
                        if download_image(img_url, save_path):
                            local_img_path = save_path
                            print(f"[TWITTER-TRACKER] Saved scraped reference image to {save_path}")
                    
                    # Save metadata
                    metadata[topic.strip()] = {
                        "scraped_image_url": img_url,
                        "local_image_path": local_img_path
                    }
                    
                    appended_count += 1
                    
        # Write metadata back
        with open(metadata_path, "w", encoding="utf-8") as mf:
            json.dump(metadata, mf, indent=2)
            
        print(f"[TWITTER-TRACKER] Update completed. Added {appended_count} new topics to topics.txt.")
    except Exception as e:
        print(f"[TWITTER-TRACKER] Failed to write new topics: {e}")

if __name__ == "__main__":
    update_topics_pool()
