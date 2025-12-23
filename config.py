import os
from dotenv import load_dotenv

load_dotenv()

# ScrapingAnt API Keys (Rotation Pool)
SCRAPINGANT_API_KEYS = [
    "644ec4afb7e04621a8d78dc80faf4da6",
    "8539601296134286839b595ab73644e4",
    "0c198162a87d4724b29b44eea3ea38ff",
    "b40ab9d289ff49ed95a61e31985f6a38",
    "af6ea4940229405eb95e234201561bc9",
]

# Gemini API Keys (Rotation Pool)
# Add multiple API keys here for automatic switching when credit runs out
# When one key's credit is exhausted, it will automatically switch to the next key
# Format: Add your API keys as strings in the list below
GEMINI_API_KEYS = [
    "AIzaSyDBA0t3mujAmX6KJIfog4YjrDHOlryhgys",  # Key 1 (replace with your key)
    # "your-second-api-key-here",  # Key 2 - uncomment and add your key
    # "your-third-api-key-here",   # Key 3 - uncomment and add your key
    # "your-fourth-api-key-here",  # Key 4 - uncomment and add your key
    # "your-fifth-api-key-here",   # Key 5 - uncomment and add your key
]

# Legacy single key support (for backward compatibility)
GEMINI_API_KEY = GEMINI_API_KEYS[0] if GEMINI_API_KEYS else None

# WordPress Credentials
WP_URL = os.getenv("WP_URL", "http://auto.local")
WP_USERNAME = os.getenv("WP_USERNAME", "ashik")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD", "Wf8o ag3e aAd4 2MZ0 dKFO pdKV")

# n8n Webhook URL (PRODUCTION)
# Important: Production URL requires workflow to be ACTIVE in n8n dashboard
# If you get 404 error, make sure the workflow is toggled ON in n8n
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "https://ashik-mama.app.n8n.cloud/webhook/amazon-master-webhook")

# Niche Keywords for Auto-Discovery
NICHE_KEYWORDS = [
    "best handheld retro gaming console 2025",
    "top rated retro game sticks for tv",
    "best budget handheld emulator under $100",
    "retro game console with built-in games review",
    "best handheld console for 90s games",
    "portable retro game console for adults",
    "best plug and play game stick 4k",
    "Anbernic RG35XX review and features",
    "best retro console for super nintendo games",
    "top 5 handheld game consoles for car trips"
]
