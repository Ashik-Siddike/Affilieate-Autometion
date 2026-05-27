"""
twitter_tracker.py
==================
Scrapes recent tweets from a curated list of tech influencers using Nitter RSS feeds.
Passes raw tweets to Gemini to extract high-quality, niche-relevant topics and appends
them to topics.txt (while ensuring no duplicates).
"""

import os
import re
import json
import random
import requests
import xml.etree.ElementTree as ET
from dotenv import load_dotenv

# Load configurations
LOCAL_ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(LOCAL_ENV_PATH, override=True)

# List of backup public Nitter instances to ensure uptime
NITTER_INSTANCES = [
    "https://nitter.privacydev.net",
    "https://nitter.poast.org",
    "https://nitter.cz",
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

def fetch_tweets_for_user(username: str) -> list[str]:
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
                    
                    tweet_text = desc.text if desc is not None and desc.text else ""
                    if not tweet_text and title is not None:
                        tweet_text = title.text
                        
                    # Clean up HTML tags
                    tweet_text = re.sub(r'<[^>]+>', ' ', tweet_text)
                    tweet_text = ' '.join(tweet_text.split())
                    
                    # Ignore retweets or empty content
                    if tweet_text and not tweet_text.startswith("RT @"):
                        # Truncate if too long (just in case)
                        tweets.append(tweet_text[:300])
                        
                if tweets:
                    print(f"[TWITTER-TRACKER] Successfully fetched {len(tweets)} tweets for @{username} via {instance}")
                    return tweets
        except Exception as e:
            # Continue trying next Nitter instance on failure
            continue
            
    print(f"[TWITTER-TRACKER] Failed to fetch tweets for @{username} from all instances.")
    return []

def extract_topics_via_gemini(tweets: list[str]) -> list[str]:
    """Uses Gemini to filter and convert raw tweets into high-quality educational topics."""
    from google import genai
    
    _raw_keys = os.getenv("GEMINI_API_KEYS", "")
    api_keys = [k.strip() for k in _raw_keys.replace("\n", ",").split(",") if k.strip()]
    if not api_keys:
        print("[TWITTER-TRACKER] Warning: No GEMINI_API_KEYS found. Cannot extract topics.")
        return []
        
    client = genai.Client(api_key=api_keys[0])
    
    tweets_block = "\n---\n".join(tweets)
    
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
4. Output a raw JSON list of strings (no Markdown tags, no ```json wrapper).
   Example output format:
   ["Topic 1 Here", "Topic 2 Here"]
"""
    
    prompt = f"Extract niche-relevant educational topics from these tweets:\n\n{tweets_block}"
    
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
            
            topics = json.loads(text)
            if isinstance(topics, list):
                return [t.strip() for t in topics if isinstance(t, str) and t.strip()]
    except Exception as e:
        print(f"[TWITTER-TRACKER] Gemini extraction failed: {e}")
        
    return []

def get_existing_topics(topics_path: str) -> list[str]:
    """Reads all current topics from topics.txt."""
    if not os.path.exists(topics_path):
        return []
    with open(topics_path, "r", encoding="utf-8") as f:
        return [line.strip().lower() for line in f if line.strip() and not line.strip().startswith("#")]

def update_topics_pool():
    """Selects random influencers, crawls their feeds, extracts new topics, and updates topics.txt."""
    print("[TWITTER-TRACKER] Starting trend-sourcing update...")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    topics_path = os.path.join(base_dir, "topics.txt")
    
    # 1. Randomly pick 5 influencers to crawl this cycle to bypass rate limits and keep it fast
    selected_users = random.sample(INFLUENCERS, min(len(INFLUENCERS), 5))
    print(f"[TWITTER-TRACKER] Curating feeds from: {selected_users}")
    
    all_raw_tweets = []
    for user in selected_users:
        tweets = fetch_tweets_for_user(user)
        all_raw_tweets.extend(tweets)
        time.sleep(1) # brief rate limiting sleep
        
    if not all_raw_tweets:
        print("[TWITTER-TRACKER] No tweets fetched in this cycle. Skipping update.")
        return
        
    # 2. Extract topics via Gemini
    new_topics = extract_topics_via_gemini(all_raw_tweets)
    if not new_topics:
        print("[TWITTER-TRACKER] No new topics extracted by Gemini.")
        return
        
    # 3. Load existing topics for duplicate check
    existing_normalized = get_existing_topics(topics_path)
    
    # 4. Append only unique topics
    appended_count = 0
    try:
        with open(topics_path, "a", encoding="utf-8") as f:
            for topic in new_topics:
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
                    appended_count += 1
                    
        print(f"[TWITTER-TRACKER] Update completed. Added {appended_count} new topics to topics.txt.")
    except Exception as e:
        print(f"[TWITTER-TRACKER] Failed to write new topics: {e}")

if __name__ == "__main__":
    update_topics_pool()
