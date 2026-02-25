import time
import scraper
import database
import ai_writer
import publisher
import schema_helper
import make_handler
# import n8n_handler (Deprecated)
from datetime import datetime, timedelta
from seo_utils import SEOChecker

# List of Test URLs (Example: Nike Shoes or similar)
TEST_URLS = [
    "https://www.amazon.com/Nike-Mens-Air-Monarch-Cross-Trainer/dp/B0007PQ16U", # Example
    # Add more URLs here
]

def get_next_keyword():
    """Reads keywords.txt and returns the first unprocessed keyword."""
    try:
        with open("keywords.txt", "r") as f:
            keywords = [line.strip() for line in f.readlines() if line.strip()]
    except FileNotFoundError:
        print("Error: keywords.txt not found.")
        return None

    try:
        with open("processed_keywords.txt", "r") as f:
            processed = {line.strip() for line in f.readlines() if line.strip()}
    except FileNotFoundError:
        processed = set()

    for kw in keywords:
        if kw not in processed:
            return kw
    
    return None

def mark_keyword_processed(keyword):
    """Appends the keyword to processed_keywords.txt."""
    with open("processed_keywords.txt", "a") as f:
        f.write(f"{keyword}\n")

def get_integer_input(prompt, default=None, min_val=1, max_val=100):
    """Gets an integer input from user with validation."""
    while True:
        if default:
            response = input(f"{prompt} (default: {default}): ").strip()
            if not response:
                return default
        else:
            response = input(f"{prompt}: ").strip()
        
        try:
            value = int(response)
            if min_val <= value <= max_val:
                return value
            else:
                print(f"⚠️  Please enter a number between {min_val} and {max_val}")
        except ValueError:
            print("⚠️  Please enter a valid number")

def get_user_preferences():
    """Asks the user for runtime preferences with advanced options."""
    print("\n" + "="*60)
    print("🤖 AMAZON AFFILIATE AUTOMATION BOT - CONFIGURATION")
    print("="*60)
    
    def get_yes_no(prompt, default=True):
        default_str = "Y/n" if default else "y/N"
        while True:
            response = input(f"{prompt} ({default_str}): ").lower().strip()
            if not response:
                return default
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            else:
                print("⚠️  Please enter 'y' or 'n'")
    
    print("\n📊 PROCESSING LIMITS (Resource Control):")
    print("-" * 60)
    config = {
        'max_keywords': get_integer_input(
            "How many keywords to process in this session?", 
            default=1, min_val=1, max_val=50
        ),
        'products_per_keyword': get_integer_input(
            "How many products to process per keyword?", 
            default=2, min_val=1, max_val=10
        ),
        'max_total_articles': get_integer_input(
            "Maximum total articles to generate (0 = unlimited)?", 
            default=5, min_val=0, max_val=100
        ),
    }
    
    print("\n⚙️  CONTENT FEATURES:")
    print("-" * 60)
    config['use_comparison'] = get_yes_no("1. Include Comparison Table? (Uses more API credits)", default=False)
    config['use_internal_links'] = get_yes_no("2. Include Internal Links? (Better SEO)", default=True)
    
    print("\n🚀 PUBLISHING OPTIONS:")
    print("-" * 60)
    config['publish_wp'] = get_yes_no("3. Publish to WordPress?", default=True)
    
    if config['publish_wp']:
        config['trigger_n8n'] = get_yes_no("4. Trigger n8n Automation (Facebook Auto-Post)?", default=True)
    else:
        config['trigger_n8n'] = False
    
    print("\n⏱️  TIMING & DELAYS:")
    print("-" * 60)
    config['delay_between_products'] = get_integer_input(
        "Delay between products (seconds)?", 
        default=3, min_val=0, max_val=60
    )
    config['delay_between_keywords'] = get_integer_input(
        "Delay between keywords (seconds)?", 
        default=5, min_val=0, max_val=120
    )
    
    print("\n📈 SUMMARY:")
    print("-" * 60)
    print(f"✅ Keywords to process: {config['max_keywords']}")
    print(f"✅ Products per keyword: {config['products_per_keyword']}")
    print(f"✅ Max total articles: {config['max_total_articles'] if config['max_total_articles'] > 0 else 'Unlimited'}")
    print(f"✅ Comparison Table: {'Yes' if config['use_comparison'] else 'No'}")
    print(f"✅ Internal Links: {'Yes' if config['use_internal_links'] else 'No'}")
    print(f"✅ WordPress Publish: {'Yes' if config['publish_wp'] else 'No'}")
    print(f"✅ n8n Automation: {'Yes' if config['trigger_n8n'] else 'No'}")
    
    confirm = get_yes_no("\n🚀 Start processing with these settings?", default=True)
    if not confirm:
        print("❌ Configuration cancelled. Exiting...")
        return None
        
    print("\n>>> Configuration confirmed! Starting bot...\n")
    return config

def get_all_unprocessed_keywords(site_keywords=None):
    """Returns all unprocessed keywords."""
    # 1. Use site-specific keywords if provided
    if site_keywords:
        keywords = [k.strip() for k in site_keywords if k.strip()]
    else:
        # Fallback to legacy file
        try:
            with open("keywords.txt", "r") as f:
                keywords = [line.strip() for line in f.readlines() if line.strip()]
        except FileNotFoundError:
            print("❌ Error: keywords.txt not found.")
            return []

    try:
        with open("processed_keywords.txt", "r") as f:
            processed = {line.strip() for line in f.readlines() if line.strip()}
    except FileNotFoundError:
        processed = set()

    unprocessed = [kw for kw in keywords if kw not in processed]
    return unprocessed


def main(config=None, log_function=print, site_config=None):
    log_function("🚀 Starting Amazon Affiliate Automation Bot...\n")
    
    if site_config:
        log_function(f"🌐 Target Site: {site_config.get('name', 'Unknown')}")
    
    # Get User Preferences if not provided
    if not config:
        # Check for AUTO_MODE environment variable
        import os
        if os.getenv("AUTO_MODE", "False").lower() == "true":
            log_function("🤖 AUTO_MODE detected. Loading default configuration...")
            config = {
                'max_keywords': 1,
                'products_per_keyword': 3,
                'max_total_articles': 3,
                'use_comparison': False,
                'use_internal_links': True,
                'publish_wp': True,
                'trigger_n8n': True,
                'delay_between_products': 5,
                'delay_between_keywords': 10
            }
        else:
            config = get_user_preferences()
            if not config:
                return
    
    # 1. Initialize Database
    database.init_db()
    log_function("✅ Database initialized.\n")

    # 2. Get unprocessed keywords
    # Pass site-specific keywords if available
    site_keywords = site_config.get('keywords', []) if site_config else None
    unprocessed_keywords = get_all_unprocessed_keywords(site_keywords)
    
    if not unprocessed_keywords:
        log_function("❌ No new keywords to process for this site.")
        return

    # Limit keywords based on user preference
    # MODIFIED: We iterate through ALL and stop when we successfully process 'max_keywords'
    keywords_to_process = unprocessed_keywords
    log_function(f"📋 Queued {len(unprocessed_keywords)} unprocessed keywords. Target: Process {config['max_keywords']} successfully.\n")

    # Track statistics
    stats = {
        'total_processed': 0,
        'articles_generated': 0,
        'articles_published': 0,
        'errors': 0
    }

    # SEO and Schedule Init
    seo_checker = SEOChecker()
    next_publish_time = datetime.now()
    interval_minutes = config.get('interval_minutes', 0)

    processed_successful_count = 0

    processed_successful_count = 0

    # Skyscraper Mode: Fetch Competitor Content
    global_competitor_text = None
    if config.get('competitor_url'):
        log_function(f"🕵️ Skyscraper Mode: Fetching {config['competitor_url']}...")
        try:
             global_competitor_text = scraper.scrape_competitor_text(config['competitor_url'])
             if global_competitor_text:
                  log_function(f"✅ Competitor content captured ({len(global_competitor_text)} chars).")
             else:
                  log_function("⚠️ Content extraction failed. Proceeding without reference.")
        except Exception as e:
             log_function(f"❌ Scraping error: {e}")

    # Process each keyword
    for keyword_idx, keyword in enumerate(keywords_to_process, 1):
        # Stop if we hit the limit of SUCCESSFUL keywords
        if processed_successful_count >= config['max_keywords']:
            log_function(f"✅ Reached keyword limit ({config['max_keywords']}). Finishing batch.")
            break
        # Check if we've reached max articles limit
        if config['max_total_articles'] > 0 and stats['articles_generated'] >= config['max_total_articles']:
            log_function(f"\n⚠️  Reached maximum article limit ({config['max_total_articles']}). Stopping.")
            break

        log_function("="*70)
        log_function(f"📌 Keyword {keyword_idx}/{len(keywords_to_process)}: {keyword}")
        log_function("="*70)
        
        # Search for products
        discovered_urls = scraper.search_amazon(keyword, limit=config['products_per_keyword'])
        
        if not discovered_urls:
            log_function(f"⚠️  No products found for '{keyword}'. Skipping.")
            mark_keyword_processed(keyword)
            continue
        
        log_function(f"✅ Found {len(discovered_urls)} product(s)\n")
        
        # Process each product
        for product_idx, url in enumerate(discovered_urls, 1):
             # Check article limit again
            if config['max_total_articles'] > 0 and stats['articles_generated'] >= config['max_total_articles']:
                log_function(f"\n⚠️  Reached maximum article limit. Moving to next keyword.")
                break
                
            log_function(f"\n{'─'*70}")
            log_function(f"📦 Product {product_idx}/{len(discovered_urls)}: {url}")
            log_function(f"{'─'*70}")
            
            # 3. Check product status
            asin = scraper.extract_asin(url)
            if not asin:
                log_function("⚠️  Invalid Amazon URL. Skipping.")
                stats['errors'] += 1
                continue
                
            status = database.check_product_status(asin)
            
            if status == 1:
                log_function(f"⏭️  Product {asin} already published. Skipping.")
                continue
            elif status == 0:
                log_function(f"🔄 Product {asin} exists but NOT published. Retrying generation...")
            
            # 4. Scrape Data
            log_function("🔍 Scraping product data...")
            product_data = scraper.get_amazon_data(url)
            
            if not product_data:
                log_function("❌ Failed to scrape data. Skipping.")
                stats['errors'] += 1
                continue
            
            log_function(f"✅ Product: {product_data.get('title', 'Unknown')[:60]}...")
            log_function(f"   Price: {product_data.get('price', 'N/A')} | Rating: {product_data.get('rating', 'N/A')}")
            
            # 5. Save to DB
            database.save_product(product_data)
            if status is None:
                log_function(f"💾 Saved {asin} to database.")
            else:
                log_function(f"💾 Updated product data for {asin}.")

            # 6. Generate AI Article
            log_function("🤖 Generating AI content...")
            
            # 6a. Fetch Comparison and Linking Data (CONDITIONAL - to save API credits)
            similar_products = None
            if config['use_comparison']:
                similar_products = database.get_similar_products(current_asin=asin, limit=2)
                log_function(f"📊 Using {len(similar_products)} similar products for comparison")
                
            internal_links = None
            if config['use_internal_links']:
                # Smart Silo Linking (Contextual)
                internal_links = database.get_relevant_posts(keyword=keyword, limit=5)
                log_function(f"🔗 Using {len(internal_links)} contextual internal links for Silo")
            
            article_content, social_data = ai_writer.generate_article(
                product_data, 
                similar_products, 
                internal_links, 
                language=config.get('language', 'English'),
                competitor_text=global_competitor_text
            )
            
            if not article_content:
                log_function("❌ Failed to generate article. Skipping.")
                stats['errors'] += 1
                continue

            stats['articles_generated'] += 1
            log_function(f"✅ Article generated successfully! ({stats['articles_generated']}/{config['max_total_articles'] if config['max_total_articles'] > 0 else '∞'})")

            # 6b. SEO Analysis
            seo_result = seo_checker.analyze(article_content, keyword)
            log_function(f"📈 SEO Score: {seo_result['score']}/100")
            if seo_result['feedback']:
                 log_function(f"   Tips: {' | '.join(seo_result['feedback'][:2])}")

            # 6.5 Generate Schema
            log_function("📋 Generating JSON-LD Schema...")
            schema_script = schema_helper.generate_product_schema(product_data)
            article_content += f"\n\n{schema_script}"

            # 7. Publish to WordPress (CONDITIONAL)
            if config['publish_wp']:
                log_function(f"🚀 Publishing to WordPress ({site_config.get('name', 'Default') if site_config else 'Default'})...")
                image_url = product_data.get('image_url')
                
                # Scheduling Logic
                publish_status = 'publish'
                publish_date_iso = None
                
                if interval_minutes > 0:
                    # Calculate future time
                    # Logic: If it's the first post, maybe publish now? Or start schedule from now + interval?
                    # Let's say first post is NOW, subsequent are spaced.
                    # Or simpler: All are spaced from now.
                    # Let's add interval for even the first one to avoid immediate blast if user wants schedule.
                    next_publish_time += timedelta(minutes=interval_minutes)
                    publish_date_iso = next_publish_time.strftime("%Y-%m-%dT%H:%M:%S")
                    publish_status = 'future'
                    log_function(f"🕒 Scheduled for: {publish_date_iso}")

                publish_result = publisher.publish_post(
                    title=f"Review: {product_data['title'][:50]}...", 
                    content=article_content,
                    image_url=image_url,
                    wp_url=site_config.get('url') if site_config else None,
                    wp_username=site_config.get('username') if site_config else None,
                    wp_password=site_config.get('app_password') if site_config else None,
                    status=publish_status,
                    publish_date=publish_date_iso
                )
        
                if isinstance(publish_result, tuple):
                    post_link, wp_image_url = publish_result
                else:
                    post_link = publish_result
                    wp_image_url = None

                if post_link:
                    log_function(f"✅ Published at: {post_link}")
                    stats['articles_published'] += 1
                    
                    # 8. Update DB to published and save link
                    database.mark_as_published(asin)
                    database.update_post_link(asin, post_link)
        
                    # 9. Trigger Make.com Automation (Replaces n8n)
                    if config['trigger_n8n']: # Variable name kept for compatibility, but triggers Make.com
                        log_function("📱 Triggering Make.com automation for Social Media...")
                        
                        # Fallback to WordPress image, then Amazon image, then dummy placeholder
                        make_image_url = wp_image_url if wp_image_url else (image_url if image_url else "https://dummyimage.com/800x800/eeeeee/333333.jpg&text=Product+Image")

                        # Construct Payload
                        make_payload = {
                            "main_title": product_data.get('title', ''),
                            "wp_link": post_link,
                            "image_url": make_image_url,
                            "fb_content": social_data.get('fb_content', ''),
                            "pin_title": social_data.get('pin_title', ''),
                            "pin_desc": social_data.get('pin_desc', ''),
                            "ig_content": social_data.get('ig_content', ''),
                            "x_content": social_data.get('x_content', '')
                        }
                        
                        # Use site-specific webhook if available
                        webhook_url = site_config.get('n8n_webhook') if site_config and site_config.get('n8n_webhook') else None
                        
                        make_success = make_handler.send_to_make_webhook(make_payload, webhook_url=webhook_url)
                        
                        if make_success:
                            log_function("✅ Make.com webhook triggered successfully!")
                            log_function("🚀 Content sent to Facebook, Pinterest, Instagram, and X.")
                        else:
                            log_function("⚠️  Make.com webhook failed - Check console logs.")
                            stats['errors'] += 1
                else:
                    log_function("❌ Publishing failed.")
                    stats['errors'] += 1
            else:
                log_function("⏭️  Skipping WordPress publishing (user preference).")
                log_function("💡 Dry run complete. Content generated but not published.")

            # Update statistics
            stats['total_processed'] += 1
            
            # Delay between products
            if product_idx < len(discovered_urls) and config['delay_between_products'] > 0:
                log_function(f"\n⏸️  Waiting {config['delay_between_products']} seconds before next product...")
                time.sleep(config['delay_between_products'])

        # After processing all products for this keyword, mark it as processed
        mark_keyword_processed(keyword)
        log_function(f"\n✅ Completed processing for keyword: {keyword}")
        log_function(f"📊 Progress: {stats['articles_generated']} articles generated, {stats['articles_published']} published")
        
        # Delay between keywords
        if keyword_idx < len(keywords_to_process) and config['delay_between_keywords'] > 0:
            log_function(f"\n⏸️  Waiting {config['delay_between_keywords']} seconds before next keyword...")
            time.sleep(config['delay_between_keywords'])
            
        # Increment success count only after processing
        processed_successful_count += 1
    
    # Final Summary
    log_function("\n" + "="*70)
    log_function("📊 FINAL SUMMARY")
    log_function("="*70)
    log_function(f"✅ Total products processed: {stats['total_processed']}")
    log_function(f"✅ Articles generated: {stats['articles_generated']}")
    log_function(f"✅ Articles published: {stats['articles_published']}")
    if stats['errors'] > 0:
        log_function(f"⚠️  Errors encountered: {stats['errors']}")
    log_function("="*70)
    log_function("🎉 Session completed!")
    
    return stats

if __name__ == "__main__":
    main()
