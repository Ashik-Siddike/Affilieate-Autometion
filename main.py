import time
import scraper
import database
import ai_writer
import publisher
import schema_helper
import make_handler
import image_composer
from datetime import datetime, timedelta
from seo_utils import SEOChecker
from niche_config import DEFAULT_NICHE, get_niche

# ---------------------------------------------------------------------------
# Keyword management (file-based fallback)
# ---------------------------------------------------------------------------
def get_next_keyword():
    """Reads keywords.txt and returns the first unprocessed keyword."""
    try:
        with open("keywords.txt", "r", encoding="utf-8") as f:
            keywords = [line.strip() for line in f.readlines() if line.strip()]
    except FileNotFoundError:
        print("Error: keywords.txt not found.")
        return None

    try:
        with open("processed_keywords.txt", "r", encoding="utf-8") as f:
            processed = {line.strip() for line in f.readlines() if line.strip()}
    except FileNotFoundError:
        processed = set()

    for kw in keywords:
        if kw not in processed:
            return kw
    return None


def mark_keyword_processed(keyword):
    """Appends the keyword to processed_keywords.txt."""
    with open("processed_keywords.txt", "a", encoding="utf-8") as f:
        f.write(f"{keyword}\n")


def get_all_unprocessed_keywords(site_keywords=None, site_id=None):
    """
    Returns all unprocessed keywords.
    Priority:
      1. site-specific keywords list
      2. Supabase keyword_pool (pending)
      3. config.py NICHE_KEYWORDS
      4. keywords.txt fallback
    """
    # 1. Site-specific keywords
    if site_keywords:
        return [k.strip() for k in site_keywords if k.strip()]

    # 2. Supabase keyword pool
    try:
        pool_keywords = database.get_pending_keywords_from_pool(site_id=site_id, limit=50)
        if pool_keywords:
            print(f"[DB] Loaded {len(pool_keywords)} keyword(s) from Supabase pool.")
            return pool_keywords
    except Exception as e:
        print(f"[WARNING] Could not fetch from Supabase pool: {e}")

    # 3. Config fallback
    try:
        from config import NICHE_KEYWORDS
        keywords = [k.strip() for kw_list in NICHE_KEYWORDS.values() for k in kw_list if k.strip()]
    except (ImportError, AttributeError):
        try:
            with open("keywords.txt", "r", encoding="utf-8") as f:
                keywords = [line.strip() for line in f.readlines() if line.strip()]
        except FileNotFoundError:
            print("[ERROR] No keywords found in Supabase, config.py, or keywords.txt.")
            return []

    try:
        with open("processed_keywords.txt", "r", encoding="utf-8") as f:
            processed = {line.strip() for line in f.readlines() if line.strip()}
    except FileNotFoundError:
        processed = set()

    unprocessed = [kw for kw in keywords if kw not in processed]
    return unprocessed


# ---------------------------------------------------------------------------
# Main bot function
# ---------------------------------------------------------------------------
def main(config=None, log_function=print, site_config=None):
    log_function("[BOT] Starting Amazon Affiliate Automation Bot...")

    if site_config:
        log_function(f"[BOT] Target Site: {site_config.get('name', 'Unknown')}")

    # Get configuration if not provided
    if not config:
        import os
        if os.getenv("AUTO_MODE", "False").lower() == "true":
            log_function("[AUTO] AUTO_MODE detected. Loading default configuration...")
            config = {
                'max_keywords':           1,
                'products_per_keyword':   3,
                'max_total_articles':     3,
                'use_comparison':         False,
                'use_internal_links':     True,
                'publish_nextjs':         True,
                'trigger_n8n':            True,
                'delay_between_products': 5,
                'delay_between_keywords': 10,
                'language':               'English',
            }
        else:
            config = get_user_preferences()
            if not config:
                return

    # Override with database site settings if they exist
    if site_config and site_config.get('settings'):
        try:
            settings = site_config['settings']
            if 'content_strategy' in settings:
                config['use_comparison'] = settings['content_strategy'].get('always_include_comparison', config['use_comparison'])
                config['language'] = settings['content_strategy'].get('language', config.get('language', 'English'))
            
            if 'publishing_rules' in settings:
                config['max_total_articles'] = settings['publishing_rules'].get('articles_per_day', config['max_total_articles'])
                config['delay_between_products'] = settings['publishing_rules'].get('delay_between_posts_minutes', config['delay_between_products']) * 60 # Convert min to sec
                
            if 'distribution' in settings:
                config['publish_nextjs'] = settings['distribution'].get('publish_to_blog', config['publish_nextjs'])
                config['trigger_n8n'] = settings['distribution'].get('post_to_facebook', config['trigger_n8n']) # Mapping facebook to n8n for now
            
            log_function("[CONFIG] Applied dynamic settings from database.")
        except Exception as e:
            log_function(f"[WARNING] Failed to parse site settings: {e}")

    # ------------------------------------------------------------------
    # 1. Initialize Database
    # ------------------------------------------------------------------
    database.init_db()
    log_function("[OK] Database initialized.")

    # ------------------------------------------------------------------
    # 2. Get unprocessed keywords
    # ------------------------------------------------------------------
    site_id = site_config.get('id') if site_config else None
    site_keywords = site_config.get('keywords', []) if site_config else None
    unprocessed_keywords = get_all_unprocessed_keywords(site_keywords, site_id=site_id)

    if not unprocessed_keywords:
        log_function("[ERROR] No new keywords to process. Please add keywords to Supabase keyword_pool.")
        return

    keywords_to_process = unprocessed_keywords
    log_function(
        f"[QUEUE] {len(unprocessed_keywords)} unprocessed keyword(s). "
        f"Target: process {config['max_keywords']} successfully."
    )

    # Track statistics
    stats = {
        'total_processed':    0,
        'articles_generated': 0,
        'articles_published': 0,
        'errors':             0,
    }

    seo_checker        = SEOChecker()
    next_publish_time  = datetime.now()
    interval_minutes   = config.get('interval_minutes', 0)
    processed_count    = 0

    # Skyscraper / competitor mode
    global_competitor_text = None
    if config.get('competitor_url'):
        log_function(f"[SKYSCRAPER] Fetching competitor: {config['competitor_url']}")
        try:
            global_competitor_text = scraper.scrape_competitor_text(config['competitor_url'])
            if global_competitor_text:
                log_function(f"[SKYSCRAPER] Captured {len(global_competitor_text)} chars.")
            else:
                log_function("[SKYSCRAPER] Content extraction failed. Continuing without reference.")
        except Exception as e:
            log_function(f"[ERROR] Competitor scraping error: {e}")

    # ------------------------------------------------------------------
    # 3. Process each keyword
    # ------------------------------------------------------------------
    for keyword_idx, keyword in enumerate(keywords_to_process, 1):

        if processed_count >= config['max_keywords']:
            log_function(f"[DONE] Reached keyword limit ({config['max_keywords']}). Finishing batch.")
            break

        if config['max_total_articles'] > 0 and stats['articles_generated'] >= config['max_total_articles']:
            log_function(f"[DONE] Reached max article limit ({config['max_total_articles']}). Stopping.")
            break

        log_function("=" * 70)
        log_function(f"[KW {keyword_idx}/{len(keywords_to_process)}] {keyword}")
        log_function("=" * 70)

        # ── Resolve active niche for this run ──
        # Priority: site_config > config dict > Supabase bot_config > DEFAULT_NICHE
        active_niche = (
            (site_config or {}).get('niche')
            or config.get('niche')
            or database.get_bot_config_value('niche', DEFAULT_NICHE)
        )
        niche_info = get_niche(active_niche)
        log_function(f"[NICHE] Active niche: '{active_niche}' ({niche_info['display_name']})")

        # Search Amazon using the active niche
        discovered_urls = scraper.search_amazon(
            keyword,
            limit=config['products_per_keyword'],
            niche_key=active_niche,
        )

        if not discovered_urls:
            log_function(f"[SKIP] No products found for '{keyword}'.")
            mark_keyword_processed(keyword)
            try:
                database.mark_keyword_completed_in_pool(keyword, site_id=site_id)
            except Exception:
                pass
            continue

        log_function(f"[FOUND] {len(discovered_urls)} product(s) discovered.")

        # Process each product for this keyword
        for product_idx, url in enumerate(discovered_urls, 1):

            if config['max_total_articles'] > 0 and stats['articles_generated'] >= config['max_total_articles']:
                log_function("[DONE] Max article limit reached. Moving to next keyword.")
                break

            log_function(f"\n{'-' * 70}")
            log_function(f"[PRODUCT {product_idx}/{len(discovered_urls)}] {url}")
            log_function(f"{'-' * 70}")

            # Extract ASIN
            asin = scraper.extract_asin(url)
            if not asin:
                log_function("[SKIP] Invalid Amazon URL.")
                stats['errors'] += 1
                continue

            # Check duplicate
            status = database.check_product_status(asin, site_id=site_id)
            if status == 1:
                log_function(f"[SKIP] {asin} already published.")
                continue
            elif status == 0:
                log_function(f"[RETRY] {asin} exists but not published. Retrying...")

            # Scrape product data
            log_function("[SCRAPE] Fetching product data from Amazon...")
            product_data = scraper.get_amazon_data(url)

            if not product_data:
                log_function("[ERROR] Failed to scrape product data. Skipping.")
                stats['errors'] += 1
                continue

            log_function(f"[SCRAPED] {product_data.get('title', 'Unknown')[:60]}")
            log_function(f"          Price: {product_data.get('price', 'N/A')} | Rating: {product_data.get('rating', 'N/A')}")

            # Save to DB
            database.save_product(product_data, site_id=site_id)
            log_function(f"[DB] Saved/Updated {asin}.")

            # Generate AI content
            log_function("[AI] Generating article content...")

            similar_products = None
            if config['use_comparison']:
                similar_products = database.get_similar_products(current_asin=asin, site_id=site_id, limit=2)
                log_function(f"[AI] Using {len(similar_products)} similar products for comparison table.")

            internal_links = None
            if config['use_internal_links']:
                internal_links = database.get_relevant_posts(keyword=keyword, site_id=site_id, limit=5)
                log_function(f"[AI] Using {len(internal_links)} internal links for silo structure.")

            article_content, social_data = ai_writer.generate_article(
                product_data,
                similar_products,
                internal_links,
                language=config.get('language', 'English'),
                competitor_text=global_competitor_text,
                affiliate_tag=site_config.get('affiliate_tracking_id') if site_config else None,
                niche_prompt=site_config.get('niche_prompt') if site_config else None
            )

            if not article_content:
                log_function("[ERROR] AI content generation failed. Skipping.")
                stats['errors'] += 1
                continue

            stats['articles_generated'] += 1
            max_art = config['max_total_articles'] if config['max_total_articles'] > 0 else 'unlimited'
            log_function(f"[AI] Article generated ({stats['articles_generated']}/{max_art}).")

            # Generate platform-specific social media captions
            log_function("[AI] Generating platform-specific social media captions...")
            
            site_domain = site_config.get('domain', 'example.com') if site_config else 'example.com'
            _tmp_post_link = f"https://{site_domain}/reviews/{product_data.get('asin','').lower()}"
            
            brand_name = product_data.get('title', '').split(' ')[0] if product_data.get('title') else 'Brand'
            
            social_captions = ai_writer.generate_social_captions(
                title=product_data.get('title', ''),
                brand=brand_name,
                amazon_url=product_data.get('product_url', ''),
                review_url=_tmp_post_link,
                niche_prompt=site_config.get('niche_prompt') if site_config else None
            )
            # Merge AI captions over any social_data from article generation
            if social_data and isinstance(social_data, dict):
                social_data.update(social_captions)
            else:
                social_data = social_captions
            log_function("[AI] ✅ Social captions ready for all platforms.")

            # Generate FAQs for rich snippets
            log_function("[AI] Generating FAQ rich snippets...")
            faqs = ai_writer.generate_faqs(
                title=product_data.get('title', ''),
                brand=brand_name,
                model_number=asin,
                niche_prompt=site_config.get('niche_prompt') if site_config else None
            )
            log_function(f"[AI] ✅ {len(faqs)} FAQ pairs generated.")

            # SEO Analysis
            seo_result = seo_checker.analyze(article_content, keyword)
            log_function(f"[SEO] Score: {seo_result['score']}/100")
            if seo_result.get('feedback'):
                log_function(f"[SEO] Tips: {' | '.join(seo_result['feedback'][:2])}")

            # Append JSON-LD Schema
            log_function("[SCHEMA] Generating JSON-LD schema...")
            schema_script   = schema_helper.generate_product_schema(product_data, faqs=faqs)
            article_content += f"\n\n{schema_script}"

            # ------------------------------------------------------------------
            # Publish to Next.js / Vercel
            # ------------------------------------------------------------------
            if config['publish_nextjs']:
                log_function("[PUBLISH] Publishing to Next.js API...")

                # Image composition
                raw_image_url = product_data.get('image_url')
                image_url     = image_composer.compose_image(raw_image_url, title=product_data.get('title'))
                pinterest_image_url = image_composer.compose_pinterest_image(raw_image_url, title=product_data.get('title'))

                # Scheduling
                publish_status   = 'publish'
                publish_date_iso = None
                if interval_minutes > 0:
                    next_publish_time += timedelta(minutes=interval_minutes)
                    publish_date_iso   = next_publish_time.strftime("%Y-%m-%dT%H:%M:%S")
                    publish_status     = 'future'
                    log_function(f"[SCHEDULE] Scheduled for: {publish_date_iso}")

                # Build slug and brand
                import re
                base_slug = re.sub(r'[^a-z0-9]+', '-', product_data['title'].lower()[:50]).strip('-')
                slug      = f"{base_slug}-{asin.lower()}"

                brand = product_data.get('title', '').split(' ')[0] if product_data.get('title') else 'Product Brand'

                publish_result = publisher.publish_post(
                    title=product_data['title'],
                    slug=slug,
                    content=article_content,
                    image_url=image_url,
                    model_number=asin,
                    brand=brand,
                    amazon_link=product_data['product_url'],
                    faqs=faqs,
                    site_url=site_config.get('url') if site_config else "https://whitlogic.online"
                )

                if isinstance(publish_result, tuple):
                    post_link, wp_image_url = publish_result
                else:
                    post_link    = publish_result
                    wp_image_url = image_url

                if post_link:
                    log_function(f"[PUBLISHED] {post_link}")
                    stats['articles_published'] += 1
                    database.mark_as_published(asin, site_id=site_id)
                    database.update_post_link(asin, post_link, site_id=site_id)

                    # Make.com social media webhook
                    if config['trigger_n8n']:
                        log_function("[MAKE] Triggering Make.com social media automation...")
                        make_image = wp_image_url or image_url or "https://dummyimage.com/800x800/eee/333.jpg&text=Product"

                        # ── Add Amazon Affiliate Tag to product URL ──
                        affiliate_tag = site_config.get('affiliate_tracking_id') if site_config else None
                        if not affiliate_tag:
                            from config import AMAZON_AFFILIATE_TAG
                            affiliate_tag = AMAZON_AFFILIATE_TAG
                            
                        product_link = product_data.get('product_url', '')
                        if affiliate_tag and product_link:
                            sep = '&' if '?' in product_link else '?'
                            product_link = f"{product_link}{sep}tag={affiliate_tag}"

                        # ── Payload must match Make.com webhook field names ──
                        make_payload = {
                            "title":            product_data.get('title', ''),
                            "url":              post_link,
                            "imageUrl":         make_image,
                            "pinterestImageUrl": pinterest_image_url,
                            "amazonUrl":        product_link,
                            "keyword":          keyword,
                            "brand":            brand,
                            "fb_content":       social_data.get('fb_content', ''),
                            "pin_title":        social_data.get('pin_title', ''),
                            "pin_desc":         social_data.get('pin_desc', ''),
                            "ig_content":       social_data.get('ig_content', ''),
                            "linkedin_content": social_data.get('linkedin_content', ''),
                        }
                        webhook_url = None
                        if site_config:
                            webhook_url = site_config.get('make_webhook_url') or site_config.get('n8n_webhook')
                            
                        make_success = make_handler.send_to_make_webhook(make_payload, webhook_url=webhook_url)

                        if make_success:
                            log_function("[MAKE] Webhook triggered — content sent to all social platforms.")
                        else:
                            log_function("[WARNING] Make.com webhook failed. Check logs.")
                            stats['errors'] += 1

                else:
                    log_function("[ERROR] Publishing failed.")
                    stats['errors'] += 1
            else:
                log_function("[DRY RUN] Skipping Next.js publishing (user preference).")

            stats['total_processed'] += 1

            # Delay between products
            if product_idx < len(discovered_urls) and config['delay_between_products'] > 0:
                log_function(f"[WAIT] {config['delay_between_products']}s before next product...")
                time.sleep(config['delay_between_products'])

        # Mark keyword as done
        mark_keyword_processed(keyword)
        try:
            database.mark_keyword_completed_in_pool(keyword, site_id=site_id)
        except Exception:
            pass
        log_function(f"[KW DONE] '{keyword}' completed.")
        log_function(f"[STATS] Generated: {stats['articles_generated']} | Published: {stats['articles_published']}")

        if keyword_idx < len(keywords_to_process) and config['delay_between_keywords'] > 0:
            log_function(f"[WAIT] {config['delay_between_keywords']}s before next keyword...")
            time.sleep(config['delay_between_keywords'])

        processed_count += 1

    # ------------------------------------------------------------------
    # Final Summary
    # ------------------------------------------------------------------
    log_function("\n" + "=" * 70)
    log_function("[SUMMARY] SESSION COMPLETE")
    log_function("=" * 70)
    log_function(f"  Total processed : {stats['total_processed']}")
    log_function(f"  Articles written: {stats['articles_generated']}")
    log_function(f"  Articles live   : {stats['articles_published']}")
    if stats['errors'] > 0:
        log_function(f"  Errors          : {stats['errors']}")
    log_function("=" * 70)

    return stats


# ---------------------------------------------------------------------------
# CLI entry point (interactive mode)
# ---------------------------------------------------------------------------
def get_user_preferences():
    """Collects runtime preferences interactively."""
    def ask_int(prompt, default, min_val=1, max_val=100):
        while True:
            resp = input(f"{prompt} (default {default}): ").strip()
            if not resp:
                return default
            try:
                v = int(resp)
                if min_val <= v <= max_val:
                    return v
                print(f"  Enter a number between {min_val} and {max_val}.")
            except ValueError:
                print("  Please enter a valid number.")

    def ask_bool(prompt, default=True):
        tag = "Y/n" if default else "y/N"
        while True:
            resp = input(f"{prompt} ({tag}): ").lower().strip()
            if not resp:
                return default
            if resp in ('y', 'yes'):
                return True
            if resp in ('n', 'no'):
                return False
            print("  Please enter 'y' or 'n'.")

    print("\n" + "=" * 60)
    print("AMAZON AFFILIATE AUTOMATION BOT - CONFIGURATION")
    print("=" * 60)

    config = {
        'max_keywords':           ask_int("Keywords to process this session?", default=1, min_val=1, max_val=50),
        'products_per_keyword':   ask_int("Products per keyword?", default=2, min_val=1, max_val=10),
        'max_total_articles':     ask_int("Max total articles (0=unlimited)?", default=5, min_val=0, max_val=100),
        'use_comparison':         ask_bool("Include comparison table?", default=False),
        'use_internal_links':     ask_bool("Include internal links?", default=True),
        'publish_nextjs':         ask_bool("Publish to Next.js API?", default=True),
        'delay_between_products': ask_int("Delay between products (sec)?", default=3, min_val=0, max_val=60),
        'delay_between_keywords': ask_int("Delay between keywords (sec)?", default=5, min_val=0, max_val=120),
    }

    if config['publish_nextjs']:
        config['trigger_n8n'] = ask_bool("Trigger Make.com automation?", default=True)
    else:
        config['trigger_n8n'] = False

    print("\nConfiguration:")
    for k, v in config.items():
        print(f"  {k}: {v}")

    if not ask_bool("\nStart with these settings?", default=True):
        print("Cancelled.")
        return None

    return config



# ---------------------------------------------------------------------------
# Telegram Alert Helper
# ---------------------------------------------------------------------------
def send_telegram_alert(message: str):
    """Sends a Telegram message if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID are set."""
    import os, requests as _req
    token   = os.getenv("TELEGRAM_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        print(f"[TELEGRAM] Skipped — token={'SET' if token else 'MISSING'}, chat_id={'SET' if chat_id else 'MISSING'}")
        return
    try:
        resp = _req.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"},
            timeout=10
        )
        if resp.status_code == 200:
            print("[TELEGRAM] ✅ Alert sent successfully.")
        else:
            print(f"[TELEGRAM] ❌ Failed! Status: {resp.status_code}, Response: {resp.text[:200]}")
    except Exception as e:
        print(f"[TELEGRAM] ❌ Error sending alert: {e}")


# ---------------------------------------------------------------------------
# Auto-Pilot Scheduler (24/7 loop)
# ---------------------------------------------------------------------------
def run_autopilot():
    """
    Runs the bot in an infinite loop for fully autonomous 24/7 operation.
    Interval is controlled by AUTOPILOT_INTERVAL_HOURS env var (default: 6).
    """
    import os, traceback

    interval_hours = float(os.getenv("AUTOPILOT_INTERVAL_HOURS", "6"))
    interval_secs  = int(interval_hours * 3600)

    # Auto-pilot config — no user input needed
    auto_config = {
        'max_keywords':           int(os.getenv("AUTO_MAX_KEYWORDS", "3")),
        'products_per_keyword':   int(os.getenv("AUTO_PRODUCTS_PER_KW", "2")),
        'max_total_articles':     int(os.getenv("AUTO_MAX_ARTICLES", "5")),
        'use_comparison':         False,
        'use_internal_links':     True,
        'publish_nextjs':         True,
        'trigger_n8n':            True,
        'delay_between_products': 5,
        'delay_between_keywords': 10,
    }

    print("=" * 60)
    print("  WHIT LOGIC — AUTO-PILOT MODE ACTIVE")
    print(f"  Cycle interval : every {interval_hours:.0f} hours")
    print(f"  Keywords/cycle : {auto_config['max_keywords']}")
    print(f"  Articles/cycle : {auto_config['max_total_articles']}")
    print("  Press Ctrl+C to stop.")
    print("=" * 60)

    send_telegram_alert(
        f"<b>Whit Logic Bot Started</b>\n"
        f"Cycle: every {interval_hours:.0f}h | "
        f"Keywords: {auto_config['max_keywords']} | "
        f"Articles: {auto_config['max_total_articles']}"
    )

    cycle = 0
    while True:
        cycle += 1
        start_time = datetime.now()
        print(f"\n[AUTOPILOT] ===== Cycle #{cycle} | {start_time.strftime('%Y-%m-%d %H:%M:%S')} =====")

        try:
            main(config=auto_config)
            elapsed = (datetime.now() - start_time).seconds // 60
            print(f"[AUTOPILOT] Cycle #{cycle} complete in {elapsed} min.")
            send_telegram_alert(
                f"<b>Cycle #{cycle} Complete</b>\n"
                f"Duration: {elapsed} min\n"
                f"Next run: {(datetime.now() + timedelta(seconds=interval_secs)).strftime('%H:%M')}"
            )
        except KeyboardInterrupt:
            print("\n[AUTOPILOT] Stopped by user.")
            send_telegram_alert("<b>Whit Logic Bot Stopped</b> (manual)")
            break
        except Exception as e:
            err_msg = traceback.format_exc()
            print(f"[AUTOPILOT] ERROR in cycle #{cycle}:\n{err_msg}")
            send_telegram_alert(
                f"<b>Bot Error — Cycle #{cycle}</b>\n"
                f"<code>{str(e)[:300]}</code>\n"
                f"Retrying in {interval_hours:.0f}h..."
            )

        # Wait for next cycle
        next_run = datetime.now() + timedelta(seconds=interval_secs)
        print(f"[AUTOPILOT] Sleeping {interval_hours:.0f}h. Next run: {next_run.strftime('%H:%M:%S')}")
        try:
            time.sleep(interval_secs)
        except KeyboardInterrupt:
            print("\n[AUTOPILOT] Stopped during sleep.")
            send_telegram_alert("<b>Whit Logic Bot Stopped</b> (during sleep)")
            break


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import os
    mode = os.getenv("RUN_MODE", "manual").lower()

    if mode == "autopilot":
        # Server / Railway deployment mode
        os.environ["AUTO_MODE"] = "True"
        run_autopilot()
    else:
        # Normal manual / GUI mode
        main()
