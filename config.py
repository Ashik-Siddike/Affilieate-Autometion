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

# Gemini API Key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyAgtcYIoSuTH_UUIcZU8SXFsJ2hjUGedpw")

# WordPress Credentials
WP_URL = os.getenv("WP_URL", "http://auto.local")
WP_USERNAME = os.getenv("WP_USERNAME", "ashik")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD", "Wf8o ag3e aAd4 2MZ0 dKFO pdKV")

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
