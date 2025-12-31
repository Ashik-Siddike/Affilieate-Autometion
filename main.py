import time
import scraper
import database
import ai_writer
import publisher
import schema_helper
import n8n_handler

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
    keywords_to_process = unprocessed_keywords[:config['max_keywords']]
    log_function(f"📋 Processing {len(keywords_to_process)} keyword(s) from {len(unprocessed_keywords)} available\n")

    # Track statistics
    stats = {
        'total_processed': 0,
        'articles_generated': 0,
        'articles_published': 0,
        'errors': 0
    }

    # Process each keyword
    for keyword_idx, keyword in enumerate(keywords_to_process, 1):
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
                internal_links = database.get_published_posts(limit=5)
                log_function(f"🔗 Using {len(internal_links)} internal links")
            
            article_content = ai_writer.generate_article(product_data, similar_products, internal_links)
            
            if not article_content:
                log_function("❌ Failed to generate article. Skipping.")
                stats['errors'] += 1
                continue

            stats['articles_generated'] += 1
            log_function(f"✅ Article generated successfully! ({stats['articles_generated']}/{config['max_total_articles'] if config['max_total_articles'] > 0 else '∞'})")

            # 6.5 Generate Schema
            log_function("📋 Generating JSON-LD Schema...")
            schema_script = schema_helper.generate_product_schema(product_data)
            article_content += f"\n\n{schema_script}"

            # 7. Publish to WordPress (CONDITIONAL)
            if config['publish_wp']:
                log_function(f"🚀 Publishing to WordPress ({site_config.get('name', 'Default') if site_config else 'Default'})...")
                image_url = product_data.get('image_url')
                
                post_link = publisher.publish_post(
                    title=f"Review: {product_data['title'][:50]}...", 
                    content=article_content,
                    image_url=image_url,
                    wp_url=site_config.get('url') if site_config else None,
                    wp_username=site_config.get('username') if site_config else None,
                    wp_password=site_config.get('app_password') if site_config else None
                )
        
                if post_link:
                    log_function(f"✅ Published at: {post_link}")
                    stats['articles_published'] += 1
                    
                    # 8. Update DB to published and save link
                    database.mark_as_published(asin)
                    database.update_post_link(asin, post_link)
        
                    # 9. Trigger n8n Automation (CONDITIONAL)
                    if config['trigger_n8n']:
                        log_function("📱 Triggering n8n automation for Facebook posting...")
                        social_caption = f"Check out our latest review: {product_data['title']}! #{keyword.replace(' ', '')} #review"
                        
                        # Use site-specific webhook if available, otherwise default
                        webhook_url = site_config.get('n8n_webhook') if site_config and site_config.get('n8n_webhook') else None
                        
                        n8n_success = n8n_handler.trigger_n8n_workflow(
                            title=product_data['title'],
                            amazon_link=post_link, 
                            image_url=image_url,
                            social_caption=social_caption,
                            category=keyword,
                            long_description=article_content,
                            webhook_url=webhook_url
                        )
                        if n8n_success:
                            log_function("✅ n8n workflow triggered successfully!")
                            log_function("📱 Facebook post should be published - Check your Facebook page")
                        else:
                            log_function("⚠️  n8n workflow failed - Check n8n dashboard for errors")
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
