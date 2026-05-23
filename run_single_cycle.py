"""
run_single_cycle.py
GitHub Actions এ একটি single bot cycle চালানোর জন্য।
Loop নেই — GitHub Actions নিজেই প্রতি 6 ঘন্টায় trigger করবে।
"""
import os
import sys
import traceback
import requests
import json

# Ensure UTF-8 output
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from main import main, send_telegram_alert
from datetime import datetime
from config import SUPABASE_URL, SUPABASE_KEY, SCRAPINGANT_API_KEYS, GEMINI_API_KEYS

def load_active_sites() -> list[dict]:
    """Fetch active sites from Supabase."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("[ERROR] Supabase credentials missing.")
        return []
    try:
        url = f"{SUPABASE_URL}/rest/v1/sites?status=eq.active&select=*"
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}"
        }
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            return r.json()
        print(f"[ERROR] Could not load sites: {r.text}")
    except Exception as e:
        print(f"[ERROR] Could not load sites from Supabase: {e}")
    return []

def run_keyword_discovery(site_config: dict):
    """Phase 0: Amazon Best Sellers + Google Trends থেকে নতুন keywords discover করে Supabase-এ save করে।"""
    try:
        from keyword_discoverer import discover_watch_keywords
        import database

        site_id = site_config.get("id")
        amazon_url = site_config.get("amazon_bestseller_url")
        niche_prompt = site_config.get("niche_prompt")

        # Supabase-এ pending keywords কতটা আছে তা চেক করি
        pending = database.get_pending_keywords_from_pool(site_id=site_id, limit=50)
        pending_count = len(pending) if pending else 0
        print(f"[CYCLE] Site '{site_config.get('name')}' - Pending keywords in pool: {pending_count}")

        # ৫টির কম থাকলে নতুন discover করি
        if pending_count < 5:
            print(f"[CYCLE] Site '{site_config.get('name')}' - Keyword pool low — starting auto-discovery...")
            
            # Phase 0a: Amazon Best Sellers থেকে
            try:
                new_kws = discover_watch_keywords(
                    limit=10, 
                    site_id=site_id, 
                    amazon_url=amazon_url, 
                    niche_prompt=niche_prompt
                )
                print(f"[CYCLE] Amazon discovery: {len(new_kws)} new keywords.")
            except Exception as e:
                print(f"[CYCLE] Amazon discovery warning: {e}")
            
            # Phase 0b: Google Trends থেকে
            # Google Trends discoverer needs to be updated per site as well, 
            # but for now we skip or run if applicable.
            try:
                from google_trends_discoverer import discover_and_save
                # We can inject site_id later into google trends, skipping for now if it doesn't support it
                pass
            except Exception as e:
                pass
        else:
            print(f"[CYCLE] Site '{site_config.get('name')}' - Keyword pool sufficient — skipping discovery.")
    except Exception as e:
        print(f"[CYCLE] Keyword discovery warning: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("  WHIT LOGIC SAAS — GitHub Actions Single Cycle")
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print("=" * 60)

    sites = load_active_sites()
    if not sites:
        print("[CYCLE] No active sites found. Exiting.")
        sys.exit(0)

    send_telegram_alert(f"🚀 <b>Autopilot Cycle Initiated!</b>\nFound {len(sites)} active sites to process.")

    total_articles = 0

    for site in sites:
        print(f"\n--- Processing Site: {site.get('name')} ---")
        
        # Inject custom API keys if present
        if site.get("gemini_api_key"):
            import config
            config.GEMINI_API_KEYS = [site.get("gemini_api_key")]
            import ai_writer
            ai_writer.GEMINI_API_KEYS = [site.get("gemini_api_key")]
        else:
            import config
            import ai_writer
            config.GEMINI_API_KEYS = GEMINI_API_KEYS
            ai_writer.GEMINI_API_KEYS = GEMINI_API_KEYS
            
        if site.get("scrapingant_api_key"):
            import keyword_discoverer
            import scraper
            keyword_discoverer.SCRAPINGANT_API_KEYS = [site.get("scrapingant_api_key")]
            scraper.SCRAPINGANT_API_KEYS = [site.get("scrapingant_api_key")]
        else:
            import keyword_discoverer
            import scraper
            keyword_discoverer.SCRAPINGANT_API_KEYS = SCRAPINGANT_API_KEYS
            scraper.SCRAPINGANT_API_KEYS = SCRAPINGANT_API_KEYS

        # Base config merged with site specific
        site_config_dict = {
            'max_keywords':           site.get("max_keywords_per_cycle", 2),
            'products_per_keyword':   site.get("products_per_kw", 2),
            'max_total_articles':     site.get("max_articles_per_cycle", 3),
            'use_comparison':         False,
            'use_internal_links':     site.get("internal_links", True),
            'publish_nextjs':         site.get("publish_to_wp", True),
            'trigger_n8n':            True,
            'delay_between_products': 5,
            'delay_between_keywords': 10,
        }

        try:
            # Phase 0
            run_keyword_discovery(site)

            # Phase 1-5
            stats = main(config=site_config_dict, site_config=site)
            if stats:
                total_articles += stats.get('articles_published', 0)
            
        except Exception as e:
            err = traceback.format_exc()
            print(f"\n❌ Error processing {site.get('name')}: {e}\n{err}")
            send_telegram_alert(f"🚨 <b>Error on site '{site.get('name')}'</b>\n<code>{str(e)[:200]}</code>")
            continue

    send_telegram_alert(
        f"✅ <b>Autopilot Cycle Complete!</b>\n"
        f"Mission successful across {len(sites)} sites.\nTotal Articles Published: {total_articles}\nGoing back to sleep! 💤☕"
    )
    print("\n✅ Multi-site cycle complete.")
