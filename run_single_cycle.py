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

