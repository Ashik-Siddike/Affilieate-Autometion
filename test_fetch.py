import requests
import json
from config import SUPABASE_URL, SUPABASE_KEY

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}

def get_posts():
    url = f"{SUPABASE_URL}/rest/v1/Post?select=id,slug,title,imageUrl"
    r = requests.get(url, headers=headers)
    print(r.status_code)
    print(r.json())

if __name__ == "__main__":
    get_posts()
