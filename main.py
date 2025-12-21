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

def get_user_preferences():
    """Asks the user for runtime preferences."""
    print("\n>>> Configuration Setup")
    
    def get_yes_no(prompt):
        while True:
            response = input(f"{prompt} (y/n): ").lower().strip()
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
    
    config = {
        'use_comparison': get_yes_no("1. Include Comparison Table?"),
        'use_internal_links': get_yes_no("2. Include Internal Links?"),
        'publish_wp': get_yes_no("3. Publish to WordPress?"),
    }
    
    if config['publish_wp']:
        config['trigger_n8n'] = get_yes_no("4. Trigger n8n Automation (Social Media)?")
    else:
        config['trigger_n8n'] = False
        
    print("\n>>> Configuration Set!")
    return config

def main():
    print("Starting Amazon Affiliate Automation Bot...")
    
    # Get User Preferences
    config = get_user_preferences()
    
    # 1. Initialize Database
    database.init_db()
    print("Database initialized.")

    # 2. Get Next Keyword
    keyword = get_next_keyword()
    
    if not keyword:
        print("No new keywords to process. Add more to keywords.txt")
        return

    print(f"\n>>> Starting discovery for Niche: {keyword}")
    
    # 2a. Search for products
    discovered_urls = scraper.search_amazon(keyword, limit=3)
    
    if not discovered_urls:
        print(f"No products found for {keyword}. Moving to next.")
        mark_keyword_processed(keyword)
        return
        
    for url in discovered_urls:
        print(f"\nProcessing Found Product: {url}")
    
        # 3. Check product status
        asin = scraper.extract_asin(url)
        if not asin:
            print("Invalid Amazon URL. Skipping.")
            continue
            
        status = database.check_product_status(asin)
        
        if status == 1:
            print(f"Product {asin} already published. Skipping.")
            continue
        elif status == 0:
            print(f"Product {asin} exists but NOT published. Retrying generation...")
        
        # 4. Scrape Data
        print("Scraping data...")
        product_data = scraper.get_amazon_data(url)
        
        if not product_data:
            print("Failed to scrape data. Skipping.")
            continue
        
        # 5. Save to DB
        database.save_product(product_data)
        if status is None:
             print(f"Saved {asin} to database.")
        else:
             print(f"Updated product data for {asin}.")

        # 6. Generate AI Article
        print("Generating AI content...")
        
        # 6a. Fetch Comparison and Linking Data (CONDITIONAL)
        similar_products = None
        if config['use_comparison']:
            similar_products = database.get_similar_products(current_asin=asin, limit=2)
            
        internal_links = None
        if config['use_internal_links']:
            internal_links = database.get_published_posts(limit=5)
        
        article_content = ai_writer.generate_article(product_data, similar_products, internal_links)
        
        if not article_content:
            print("Failed to generate article. Skipping publishing.")
            continue

        # 6.5 Generate Schema
        print("Generating JSON-LD Schema...")
        schema_script = schema_helper.generate_product_schema(product_data)
        article_content += f"\n\n{schema_script}"

        # 7. Publish to WordPress (CONDITIONAL)
        if config['publish_wp']:
            print("Publishing to WordPress...")
            image_url = product_data.get('image_url')
            
            post_link = publisher.publish_post(
                title=f"Review: {product_data['title'][:50]}...", 
                content=article_content,
                image_url=image_url
            )
    
            if post_link:
                print(f"Published at: {post_link}")
                
                # 8. Update DB to published and save link
                database.mark_as_published(asin)
                database.update_post_link(asin, post_link)
                print("Marked as published in DB and link saved.")
    
                # 9. Trigger n8n Automation (CONDITIONAL)
                if config['trigger_n8n']:
                    print("Triggering n8n automation...")
                    social_caption = f"Check out our latest review: {product_data['title']}! #retro #gaming #review"
                    # We pass the 'keyword' as category, or we could scrape it. 
                    # Keyword is a good proxy for Niche/Category.
                    n8n_handler.trigger_n8n_workflow(
                        title=product_data['title'],
                        amazon_link=post_link, 
                        image_url=image_url,
                        social_caption=social_caption,
                        category=keyword,
                        long_description=article_content
                    )
            else:
                print("Publishing failed.")
        else:
            print("Skipping WordPress publishing key user preference.")
            # We might want to save the content locally or just dry run.
            print("Dry run complete. Content generated but not published.")

        # 9. Sleep between tasks to be polite
        print("Sleeping for 5 seconds...")
        time.sleep(5)

    # After processing all products for this keyword (or attempting to), mark it as processed
    mark_keyword_processed(keyword)
    print(f"\nCompleted processing for keyword: {keyword}")

if __name__ == "__main__":
    main()
