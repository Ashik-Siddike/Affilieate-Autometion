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
    "AIzaSyBZMwE3GSn2FcFPaIe8ryvYCNYIFm3C0Dw",  # Key 1 (replace with your key)
    "AIzaSyAZKIWu0L91cy04No6pSMhLmfNkAsx75Kw",  # Key 2 - uncomment and add your key
    "AIzaSyCW1pScKpPGHLH4KMqbmFYMjTChwsDMcgM",  # Key 3 - uncomment and add your key
    "AIzaSyB2ob5CxnMldLZ0a2L7LoiapGC-hEnKZ0o",  # Key 4 - uncomment and add your key
    "AIzaSyAkknQk90V8DjabxLYSPYHgJFCh_QzEca0",  # Key 5 - uncomment and add your key
    "AIzaSyCS25geg3Z-pEfNhpFStZPuRB1Ah1U7Oyk",  # Key 6 - uncomment and add your key
    "AIzaSyAe8FGWbWSBeYtYFmCXEZjVmhfQ7ljb7Eg",  # Key 7 - uncomment and add your key
    "AIzaSyCrtUVKvOf8__XGWbAUHl8QXP_ngYOfKd8",  # Key 8 - uncomment and add your key
]

# Legacy single key support (for backward compatibility)
GEMINI_API_KEY = GEMINI_API_KEYS[0] if GEMINI_API_KEYS else None

# WordPress Credentials
WP_URL = os.getenv("WP_URL", "https://automation-project.cstjpi.xyz/")
WP_USERNAME = os.getenv("WP_USERNAME", "ashik")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD", "Q65c e8pR 4P9z uh0g Zc4g ac2g")

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
