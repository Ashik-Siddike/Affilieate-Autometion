"""
run_single_cycle.py
===================
GitHub Actions এ একটি single bot cycle চালানোর জন্য।
Loop নেই — GitHub Actions নিজেই প্রতি 6 ঘন্টায় trigger করবে।

Pipeline routing:
  - source_type = "twitter"  →  twitter_pipeline.py
  - source_type = "amazon"   →  main.py (Amazon affiliate)
  - source_type unset        →  both pipelines
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
    """Fetch all active sites from Supabase."""
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
    """
    Phase 0 (Amazon mode): Amazon Best Sellers + Google Trends থেকে
    নতুন keywords discover করে Supabase-এ save করে।
    """
    try:
        from keyword_discoverer import discover_watch_keywords
        import database

        site_id = site_config.get("id")
        amazon_url = site_config.get("amazon_bestseller_url")
        niche_prompt = site_config.get("niche_prompt")

        pending = database.get_pending_keywords_from_pool(site_id=site_id, limit=50)
        pending_count = len(pending) if pending else 0
        print(f"[CYCLE] Site '{site_config.get('name')}' — Pending keywords: {pending_count}")

        if pending_count < 5:
            print(f"[CYCLE] Keyword pool low — starting auto-discovery...")
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
        else:
            print(f"[CYCLE] Keyword pool sufficient — skipping discovery.")
    except Exception as e:
        print(f"[CYCLE] Keyword discovery warning: {e}")


def inject_api_keys(site: dict):
    """Injects site-specific or global API keys into modules."""
    import config
    import ai_writer

    # Gemini keys
    if site.get("gemini_api_key"):
        config.GEMINI_API_KEYS = [site["gemini_api_key"]]
        ai_writer.GEMINI_API_KEYS = [site["gemini_api_key"]]
    else:
        config.GEMINI_API_KEYS = GEMINI_API_KEYS
        ai_writer.GEMINI_API_KEYS = GEMINI_API_KEYS

    # ScrapingAnt keys (Amazon pipeline only)
    try:
        import keyword_discoverer
        import scraper
        if site.get("scrapingant_api_key"):
            keyword_discoverer.SCRAPINGANT_API_KEYS = [site["scrapingant_api_key"]]
            scraper.SCRAPINGANT_API_KEYS = [site["scrapingant_api_key"]]
        else:
            keyword_discoverer.SCRAPINGANT_API_KEYS = SCRAPINGANT_API_KEYS
            scraper.SCRAPINGANT_API_KEYS = SCRAPINGANT_API_KEYS
    except ImportError:
        pass


def run_amazon_pipeline(site: dict) -> int:
    """
    Runs the Amazon Affiliate pipeline for a site.
    Returns number of articles published.
    """
    inject_api_keys(site)

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

    # Phase 0: Keyword discovery
    run_keyword_discovery(site)

    # Phase 1-5: Amazon → Article → Publish
    stats = main(config=site_config_dict, site_config=site)
    return stats.get('articles_published', 0) if stats else 0


def run_twitter_pipeline_for_site(site: dict) -> int:
    """
    Runs the Twitter → Blog pipeline for a site.
    Returns number of blogs published.
    """
    inject_api_keys(site)

    try:
        from twitter_pipeline import run_twitter_pipeline

        max_blogs = site.get("max_articles_per_cycle", 3)
        stats = run_twitter_pipeline(
            site_config=site,
            max_blogs=max_blogs,
        )
        return stats.get('blogs_published', 0)
    except Exception as e:
        print(f"[CYCLE] Twitter pipeline error: {e}")
        traceback.print_exc()
        return 0


if __name__ == "__main__":
    print("=" * 65)
    print("  🤖 AFFILIATE AUTOMATION — GitHub Actions Single Cycle")
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print("=" * 65)

    # ── Determine run mode from environment ───────────────────────────────────
    # RUN_PIPELINE env var: "amazon" | "twitter" | "all" (default: "all")
    run_pipeline = os.getenv("RUN_PIPELINE", "all").lower()
    print(f"[CYCLE] Pipeline mode: {run_pipeline}")

    # ── Load active sites ─────────────────────────────────────────────────────
    sites = load_active_sites()

    if not sites:
        print("[CYCLE] ⚠️  No active sites in Supabase. Running in single-site env mode.")
        # Create a default site from environment variables
        default_source = os.getenv("SOURCE_TYPE", "amazon").lower()
        sites = [{
            "id": None,
            "name": os.getenv("SITE_NAME", "My Blog"),
            "url": os.getenv("SITE_URL", "https://auto-blogging-site.vercel.app"),
            "domain": os.getenv("SITE_URL", "auto-blogging-site.vercel.app"),
            "niche": os.getenv("SITE_NICHE", "technology"),
            "niche_prompt": os.getenv("SITE_NICHE", ""),
            "language": "English",
            "source_type": default_source,
            "api_url": os.getenv("NEXT_API_URL", "https://auto-blogging-site.vercel.app/api/posts"),
            "bot_api_secret": os.getenv("BOT_API_SECRET", ""),
            "twitter_handles": os.getenv("TWITTER_HANDLES", "").split(",") if os.getenv("TWITTER_HANDLES") else [],
            "max_keywords_per_cycle": int(os.getenv("AUTO_MAX_KEYWORDS", "2")),
            "products_per_kw": int(os.getenv("AUTO_PRODUCTS_PER_KW", "2")),
            "max_articles_per_cycle": int(os.getenv("AUTO_MAX_ARTICLES", "3")),
            "publish_to_wp": True,
        }]

    send_telegram_alert(
        f"🚀 <b>Autopilot Cycle Started!</b>\n"
        f"Sites: {len(sites)} | Mode: {run_pipeline}\n"
        f"Time: {datetime.now().strftime('%H:%M')} UTC"
    )

    total_articles = 0

    for site in sites:
        site_name = site.get('name', 'Unknown')
        source_type = site.get('source_type', 'amazon').lower()

        print(f"\n{'—' * 60}")
        print(f"[CYCLE] 🌐 Site: {site_name} | Source: {source_type}")
        print(f"{'—' * 60}")

        try:
            published = 0

            # ── Route to correct pipeline based on source_type ────────────────
            if run_pipeline == "twitter" or (run_pipeline == "all" and source_type == "twitter"):
                # Twitter → Blog pipeline
                print(f"[CYCLE] 🐦 Starting Twitter pipeline...")
                published = run_twitter_pipeline_for_site(site)

            elif run_pipeline == "amazon" or (run_pipeline == "all" and source_type in ["amazon", ""]):
                # Amazon → Affiliate Review pipeline
                print(f"[CYCLE] 🛒 Starting Amazon pipeline...")
                published = run_amazon_pipeline(site)

            elif run_pipeline == "all":
                # Run both pipelines for sites without explicit source_type
                print(f"[CYCLE] 🔄 Running both pipelines...")
                amazon_count = run_amazon_pipeline(site)
                twitter_count = run_twitter_pipeline_for_site(site)
                published = amazon_count + twitter_count

            total_articles += published
            print(f"[CYCLE] ✅ Site '{site_name}' complete. Published: {published}")

        except Exception as e:
            err = traceback.format_exc()
            print(f"\n❌ Error processing {site_name}: {e}\n{err}")
            send_telegram_alert(
                f"🚨 <b>Error on '{site_name}'</b>\n"
                f"<code>{str(e)[:200]}</code>"
            )
            continue

    # ── Final summary ─────────────────────────────────────────────────────────
    send_telegram_alert(
        f"✅ <b>Autopilot Cycle Complete!</b>\n"
        f"Sites: {len(sites)} | Total Published: {total_articles}\n"
        f"Going back to sleep 💤☕"
    )
    print(f"\n✅ Cycle complete. Total published: {total_articles}")
