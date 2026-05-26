import os
from dotenv import load_dotenv
import requests

load_dotenv()
SCRAPINGANT_API_KEYS = [k.strip() for k in os.getenv("SCRAPINGANT_API_KEYS", "").replace("\n", ",").split(",") if k.strip()]
key = SCRAPINGANT_API_KEYS[0]

url = "https://www.amazon.com/Best-Sellers-Watches/zgbs/fashion/6358539011/"
print(f"Fetching {url} with key {key}...")
resp = requests.get(
    "https://api.scrapingant.com/v2/general",
    params={"url": url, "x-api-key": key, "browser": "true"},
    timeout=30
)

print(f"Status: {resp.status_code}")
html = resp.text
print(f"HTML Length: {len(html)}")

# Check if there's any text looking like a product title
import re
titles = re.findall(r'data-p13n-asin-metadata="([^"]+)"', html)
print(f"p13n blocks found: {len(titles)}")

# Save to file to inspect later if needed
with open("scratch/scraped.html", "w", encoding="utf-8") as f:
    f.write(html)
