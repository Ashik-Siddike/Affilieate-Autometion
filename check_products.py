import requests
from config import SUPABASE_URL, SUPABASE_KEY

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}

def check_products():
    url = f"{SUPABASE_URL}/rest/v1/products?select=asin,title,image_url,post_link&limit=5"
    r = requests.get(url, headers=headers)
    import pprint
    pprint.pprint(r.json())

if __name__ == "__main__":
    check_products()
