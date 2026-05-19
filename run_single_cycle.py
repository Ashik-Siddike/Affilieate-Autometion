"""
run_single_cycle.py
GitHub Actions এ একটি single bot cycle চালানোর জন্য।
Loop নেই — GitHub Actions নিজেই প্রতি 6 ঘন্টায় trigger করবে।
"""
import os
import sys
import traceback

# Ensure UTF-8 output
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from main import main, send_telegram_alert
from datetime import datetime

def run_keyword_discovery():
    """Phase 0: Amazon Best Sellers থেকে নতুন keywords discover করে Supabase-এ save করে।"""
    try:
        from keyword_discoverer import discover_watch_keywords
        import database

        # Supabase-এ pending keywords কতটা আছে তা চেক করি
        pending = database.get_pending_keywords(limit=50)
        pending_count = len(pending) if pending else 0
        print(f"[CYCLE] Pending keywords in pool: {pending_count}")

        # ৫টির কম থাকলে নতুন discover করি
        if pending_count < 5:
            print("[CYCLE] Keyword pool low — starting auto-discovery from Amazon Best Sellers...")
            new_kws = discover_watch_keywords(limit=20)
            print(f"[CYCLE] Discovered & saved {len(new_kws)} new keywords.")
        else:
            print("[CYCLE] Keyword pool sufficient — skipping discovery.")
    except Exception as e:
        print(f"[CYCLE] Keyword discovery warning: {e}")

def load_config_from_supabase() -> dict:
    """Supabase bot_config table থেকে settings পড়ে। Failure হলে defaults ব্যবহার করে।"""
    defaults = {
        "max_keywords":      2,
        "max_articles":      4,
        "products_per_kw":   2,
        "is_paused":         False,
        "publish_to_social": True,
    }
    try:
        import requests
        from config import SUPABASE_URL, SUPABASE_KEY
        if not SUPABASE_URL or not SUPABASE_KEY:
            return defaults
        r = requests.get(
            f"{SUPABASE_URL}/rest/v1/bot_config?select=key,value",
            headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"},
            timeout=10
        )
        if r.status_code == 200:
            raw = {row["key"]: row["value"] for row in r.json()}
            return {
                "max_keywords":      int(raw.get("max_keywords",      defaults["max_keywords"])),
                "max_articles":      int(raw.get("max_articles",      defaults["max_articles"])),
                "products_per_kw":   int(raw.get("products_per_kw",   defaults["products_per_kw"])),
                "is_paused":         raw.get("is_paused", "false").lower() == "true",
                "publish_to_social": raw.get("publish_to_social", "true").lower() == "true",
            }
    except Exception as e:
        print(f"[CYCLE] Could not load config from Supabase: {e}. Using defaults.")
    return defaults

if __name__ == "__main__":
    print("=" * 60)
    print("  WHIT LOGIC — GitHub Actions Single Cycle")
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print("=" * 60)

    config = {
        'max_keywords':           int(os.getenv("AUTO_MAX_KEYWORDS", "2")),
        'products_per_keyword':   int(os.getenv("AUTO_PRODUCTS_PER_KW", "2")),
        'max_total_articles':     int(os.getenv("AUTO_MAX_ARTICLES", "4")),
        'use_comparison':         False,
        'use_internal_links':     True,
        'publish_nextjs':         True,
        'trigger_n8n':            True,
        'delay_between_products': 5,
        'delay_between_keywords': 10,
    }

    # ── Load settings from Supabase bot_config (overrides defaults) ──
    db_cfg = load_config_from_supabase()
    print(f"[CYCLE] Loaded config from Supabase: {db_cfg}")

    if db_cfg.get("is_paused", False):
        send_telegram_alert("<b>⏸️ Bot is PAUSED</b>\nSettings-এ Pause করা আছে। Cycle skip হলো।")
        print("[CYCLE] Bot is PAUSED via Supabase config. Exiting.")
        sys.exit(0)

    config['max_keywords']       = db_cfg.get("max_keywords",    config['max_keywords'])
    config['max_total_articles'] = db_cfg.get("max_articles",    config['max_total_articles'])
    config['products_per_keyword'] = db_cfg.get("products_per_kw", config['products_per_keyword'])
    config['trigger_n8n']        = db_cfg.get("publish_to_social", True)

    try:
        send_telegram_alert(
            f"<b>GitHub Actions Cycle Started</b>\n"
            f"Time: {datetime.now().strftime('%H:%M')} UTC\n"
            f"Keywords: {config['max_keywords']} | Articles: {config['max_total_articles']}"
        )

        # ── Phase 0: Auto-discover keywords if pool is low ──
        run_keyword_discovery()

        # ── Phase 1–5: Scrape → Write → Publish ──
        main(config=config)


        send_telegram_alert(
            f"<b>GitHub Actions Cycle Complete ✅</b>\n"
            f"Time: {datetime.now().strftime('%H:%M')} UTC"
        )
        print("\n✅ Cycle complete.")
    except Exception as e:
        err = traceback.format_exc()
        print(f"\n❌ Error: {e}\n{err}")
        send_telegram_alert(
            f"<b>GitHub Actions Error ❌</b>\n"
            f"<code>{str(e)[:300]}</code>"
        )
        sys.exit(1)

