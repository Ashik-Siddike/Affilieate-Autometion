import requests
import re
from config import SCRAPINGANT_API_KEYS
import time
from urllib.parse import quote_plus

def check_rank(keyword, target_domain):
    """
    Checks the ranking of a domain for a keyword on Google using ScrapingAnt.
    Returns: (rank, url_found) or (None, None)
    """
    if not SCRAPINGANT_API_KEYS:
        return None, "No API Keys"

    # Clean domain
    target_domain = target_domain.replace("https://", "").replace("http://", "").split("/")[0]
    
    encoded_keyword = quote_plus(keyword)
    search_url = f"https://www.google.com/search?q={encoded_keyword}&num=100&hl=en&gl=us"
    
    print(f"🔍 Checking Rank for '{keyword}' on '{target_domain}'...")

    for api_key in SCRAPINGANT_API_KEYS:
        try:
            # We use ScrapingAnt to bypass CAPTCHA
            response = requests.get(
                "https://api.scrapingant.com/v2/general",
                params={
                    'url': search_url,
                    'browser': 'true',  # Google needs browser rendering often
                    'proxy_type': 'residential', # Better for Google
                    'proxy_country': 'US'
                },
                headers={'x-api-key': api_key},
                timeout=60
            )

            if response.status_code == 200:
                html = response.text
                
                # Check for CAPTCHA/Block
                if "Our systems have detected unusual traffic" in html:
                    print("⚠️ Google Blocked Request.")
                    continue

                # Regex to find links in search results
                # Google usually has <a href="/url?q=..." or <a href="https://..."
                # Main results often in <div class="g"> ... <a href="...">
                # We'll just look for all links and filter
                # Simple pattern: href="(https?://[^"]+)"
                
                links = re.findall(r'href="(https?://[^"]+)"', html)
                
                rank = 0
                real_rank = 0
                found = False
                found_url = None
                
                seen_domains = set()

                for link in links:
                    # Filter junk (google links, cache, etc)
                    if "google.com" in link or "youtube.com" in link:
                        continue
                        
                    # Basic cleanup
                    if "/search" in link or "webcache" in link:
                        continue

                    # Extract domain from link to deduplicate
                    try:
                        link_domain = link.split("//")[1].split("/")[0]
                    except:
                        continue
                        
                    if link_domain not in seen_domains:
                        seen_domains.add(link_domain)
                        real_rank += 1
                        
                        if target_domain in link_domain:
                            found = True
                            rank = real_rank
                            found_url = link
                            break
                
                if found:
                    print(f"✅ Found at Rank #{rank} ({found_url})")
                    return rank, found_url
                else:
                    print(f"❌ Not found in top {real_rank} results.")
                    return 0, None
            
            elif response.status_code == 429:
                continue
            else:
                print(f"Error {response.status_code}: {response.text}")
                continue

        except Exception as e:
            print(f"Error checking rank: {e}")
            continue

    return None, None
