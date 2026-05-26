import re

with open('main.py', 'r', encoding='utf-8') as f:
    code = f.read()

code = re.sub(
    r'def get_all_unprocessed_keywords\(site_keywords=None\):',
    r'def get_all_unprocessed_keywords(site_keywords=None, site_id=None):',
    code
)
code = re.sub(
    r'pool_keywords = database\.get_pending_keywords_from_pool\(limit=50\)',
    r'pool_keywords = database.get_pending_keywords_from_pool(site_id=site_id, limit=50)',
    code
)

# In main(): site_id is site_config.get('id') if site_config else None
code = re.sub(
    r'def main\(config=None, log_function=None, site_config=None\):',
    r'def main(config=None, log_function=None, site_config=None):\n    site_id = site_config.get("id") if site_config else None\n    site_niche = site_config.get("niche_prompt") if site_config else None',
    code
)

code = re.sub(
    r'keywords_to_process = get_all_unprocessed_keywords\(site_keywords\)',
    r'keywords_to_process = get_all_unprocessed_keywords(site_keywords, site_id=site_id)',
    code
)

code = re.sub(
    r'pool_count = database\.check_keyword_pool_count\(\)',
    r'pool_count = database.check_keyword_pool_count(site_id=site_id)',
    code
)

code = re.sub(
    r'database\.mark_keyword_completed_in_pool\(keyword\)',
    r'database.mark_keyword_completed_in_pool(keyword, site_id=site_id)',
    code
)

code = re.sub(
    r'status = database\.check_product_status\(asin\)',
    r'status = database.check_product_status(asin, site_id=site_id)',
    code
)

code = re.sub(
    r'database\.save_product\(product_data\)',
    r'database.save_product(product_data, site_id=site_id)',
    code
)

code = re.sub(
    r'similar_products = database\.get_similar_products\(current_asin=asin, limit=2\)',
    r'similar_products = database.get_similar_products(current_asin=asin, site_id=site_id, limit=2)',
    code
)

code = re.sub(
    r'internal_links = database\.get_relevant_posts\(keyword=keyword, limit=5\)',
    r'internal_links = database.get_relevant_posts(keyword=keyword, site_id=site_id, limit=5)',
    code
)

code = re.sub(
    r'database\.mark_as_published\(asin\)',
    r'database.mark_as_published(asin, site_id=site_id)',
    code
)

code = re.sub(
    r'database\.update_post_link\(asin, post_link\)',
    r'database.update_post_link(asin, post_link, site_id=site_id)',
    code
)

# Niche extraction fallback replacement
code = re.sub(
    r'niche_context = config\.get\("niche"\) \\\n\s*or database\.get_bot_config_value\(\'niche\', DEFAULT_NICHE\) \\\n\s*or get_niche\(\)',
    r'niche_context = site_niche or config.get("niche") or get_niche()',
    code
)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("main.py refactored.")
