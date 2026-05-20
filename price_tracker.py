import requests
import time
import re
from config import NEXT_API_URL, BOT_API_SECRET
import scraper
import database

def parse_price(price_str):
    """Extracts numeric value from a price string like '$19.99' or '£19.99'."""
    if not price_str:
        return None
    match = re.search(r'[\d,]+\.\d{2}', price_str)
    if match:
        try:
            return float(match.group().replace(',', ''))
        except ValueError:
            return None
    return None

def check_prices():
    print("=" * 60)
    print("🔥 STARTING LIVE PRICE TRACKER")
    print("=" * 60)
    
    # Get published products from Supabase
    try:
        url = f"{database.SUPABASE_URL}/rest/v1/products?is_published=eq.true&select=asin,title,price,product_url"
        response = requests.get(url, headers=database.get_headers(), timeout=10)
        products = response.json()
    except Exception as e:
        print(f"[ERROR] Failed to fetch products from DB: {e}")
        return

    print(f"Found {len(products)} published products to track.")
    
    for idx, prod in enumerate(products, 1):
        asin = prod.get('asin')
        old_price_str = prod.get('price')
        url = prod.get('product_url')
        
        old_price = parse_price(old_price_str)
        if not old_price or not url:
            print(f"[{idx}/{len(products)}] Skipping {asin} - Invalid old price or URL.")
            continue
            
        print(f"[{idx}/{len(products)}] Checking {asin} (Old: {old_price_str})...")
        
        # Scrape current data
        new_data = scraper.get_amazon_data(url)
        if not new_data:
            print(f"  [ERROR] Failed to scrape {asin}.")
            time.sleep(3)
            continue
            
        new_price_str = new_data.get('price')
        new_price = parse_price(new_price_str)
        
        if not new_price:
            print(f"  [WARNING] Could not parse new price for {asin}: {new_price_str}")
            time.sleep(3)
            continue
            
        print(f"  Current: {new_price_str}")
        
        if new_price < old_price:
            discount = ((old_price - new_price) / old_price) * 100
            if discount >= 5: # Only flag if discount is at least 5%
                discount_str = f"{int(discount)}%"
                print(f"  🔥 DEAL FOUND! {discount_str} OFF!")
                
                # Update Next.js API
                try:
                    patch_url = NEXT_API_URL
                    headers = {
                        'Content-Type': 'application/json',
                        'x-bot-api-secret': BOT_API_SECRET
                    }
                    payload = {
                        "modelNumber": asin,
                        "isDeal": True,
                        "discountPercentage": discount_str
                    }
                    res = requests.patch(patch_url, headers=headers, json=payload, timeout=10)
                    if res.status_code == 200:
                        print("  [API] Successfully updated Deal status on website!")
                    else:
                        print(f"  [API ERROR] {res.status_code}: {res.text}")
                except Exception as e:
                    print(f"  [API ERROR] {e}")
            else:
                print(f"  Minor drop ({int(discount)}%), ignoring.")
        else:
            print("  No deal.")
            
            # Optionally remove deal if price went back up
            if new_price >= old_price:
                try:
                    patch_url = NEXT_API_URL
                    headers = {
                        'Content-Type': 'application/json',
                        'x-bot-api-secret': BOT_API_SECRET
                    }
                    payload = {
                        "modelNumber": asin,
                        "isDeal": False,
                        "discountPercentage": None
                    }
                    requests.patch(patch_url, headers=headers, json=payload, timeout=10)
                except:
                    pass

        time.sleep(4) # Delay to respect rate limits

    print("=" * 60)
    print("✅ PRICE TRACKING COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    database.init_db()
    check_prices()
