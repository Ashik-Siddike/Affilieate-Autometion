import os
from dotenv import load_dotenv

load_dotenv()

# ScrapingAnt API Keys (Rotation Pool)
# Loaded from .env file (Comma separated)
_scraping_keys_str = os.getenv("SCRAPINGANT_API_KEYS", "")
SCRAPINGANT_API_KEYS = [k.strip() for k in _scraping_keys_str.split(",") if k.strip()]

# Gemini API Keys (Rotation Pool)
# Loaded from .env file (Comma separated)
_gemini_keys_str = os.getenv("GEMINI_API_KEYS", "")
GEMINI_API_KEYS = [k.strip() for k in _gemini_keys_str.split(",") if k.strip()]

# Legacy single key support (for backward compatibility)
GEMINI_API_KEY = GEMINI_API_KEYS[0] if GEMINI_API_KEYS else None

# WordPress Credentials
WP_URL = os.getenv("WP_URL", "https://little-angels-hub.wasmer.app/")
WP_USERNAME = os.getenv("WP_USERNAME", "ashik-siddike")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD", "h9lp oh9Z 6fKi C5bx RoZr z3jl")

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

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Automation Key
AUTO_KEY = os.getenv("AUTO_KEY")
