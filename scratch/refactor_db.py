import re

with open('database.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Refactoring check_product_status
code = re.sub(r'def check_product_status\(asin\):', r'def check_product_status(asin, site_id=None):', code)
code = re.sub(r'url = f"\{SUPABASE_URL\}/rest/v1/products\?asin=eq\.\{asin\}&select=is_published"',
              r'url = f"{SUPABASE_URL}/rest/v1/products?asin=eq.{asin}&select=is_published" + (f"&site_id=eq.{site_id}" if site_id else "")', code)

# Refactoring save_product
code = re.sub(r'def save_product\(data_dict\):', r'def save_product(data_dict, site_id=None):', code)
code = re.sub(r'"product_url":  data_dict\.get\(\'product_url\'\),',
              r'"product_url":  data_dict.get(\'product_url\'),\n            "site_id": site_id,', code)

# Refactoring mark_as_published
code = re.sub(r'def mark_as_published\(asin\):', r'def mark_as_published(asin, site_id=None):', code)
code = re.sub(r'url = f"\{SUPABASE_URL\}/rest/v1/products\?asin=eq\.\{asin\}"',
              r'url = f"{SUPABASE_URL}/rest/v1/products?asin=eq.{asin}" + (f"&site_id=eq.{site_id}" if site_id else "")', code)

# Refactoring update_post_link
code = re.sub(r'def update_post_link\(asin, post_link\):', r'def update_post_link(asin, post_link, site_id=None):', code)

# Refactoring get_similar_products
code = re.sub(r'def get_similar_products\(current_asin, limit=2\):', r'def get_similar_products(current_asin, site_id=None, limit=2):', code)
code = re.sub(r'f"&limit=20"', r'f"&limit=20" + (f"&site_id=eq.{site_id}" if site_id else "")', code)

# Refactoring get_published_posts
code = re.sub(r'def get_published_posts\(limit=5\):', r'def get_published_posts(site_id=None, limit=5):', code)
code = re.sub(r'f"&limit=\{limit\}"', r'f"&limit={limit}" + (f"&site_id=eq.{site_id}" if site_id else "")', code)

# Refactoring get_relevant_posts
code = re.sub(r'def get_relevant_posts\(keyword, limit=5\):', r'def get_relevant_posts(keyword, site_id=None, limit=5):', code)
code = re.sub(r'recent = get_published_posts\(limit=limit\)', r'recent = get_published_posts(site_id=site_id, limit=limit)', code)
code = re.sub(r'return get_published_posts\(limit\)', r'return get_published_posts(site_id=site_id, limit=limit)', code)

# Refactoring check_keyword_pool_count
code = re.sub(r'def check_keyword_pool_count\(\):', r'def check_keyword_pool_count(site_id=None):', code)
code = re.sub(r'count_url = f"\{SUPABASE_URL\}/rest/v1/keyword_pool\?status=eq\.pending&select=keyword"',
              r'count_url = f"{SUPABASE_URL}/rest/v1/keyword_pool?status=eq.pending&select=keyword" + (f"&site_id=eq.{site_id}" if site_id else "")', code)

# Refactoring get_pending_keywords_from_pool
code = re.sub(r'def get_pending_keywords_from_pool\(limit=10\):', r'def get_pending_keywords_from_pool(site_id=None, limit=10):', code)

# Refactoring add_keywords_to_pool
code = re.sub(r'def add_keywords_to_pool\(keywords\):', r'def add_keywords_to_pool(keywords, site_id=None):', code)
code = re.sub(r'payload = \[\{"id": str\(uuid\.uuid4\(\)\), "keyword": kw, "status": "pending"\} for kw in keywords\]',
              r'payload = [{"id": str(uuid.uuid4()), "keyword": kw, "status": "pending", "site_id": site_id} for kw in keywords]', code)

# Refactoring mark_keyword_completed_in_pool
code = re.sub(r'def mark_keyword_completed_in_pool\(keyword\):', r'def mark_keyword_completed_in_pool(keyword, site_id=None):', code)
code = re.sub(r'url = f"\{SUPABASE_URL\}/rest/v1/keyword_pool\?keyword=eq\.\{keyword\}"',
              r'url = f"{SUPABASE_URL}/rest/v1/keyword_pool?keyword=eq.{keyword}" + (f"&site_id=eq.{site_id}" if site_id else "")', code)


with open('database.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("database.py refactored successfully.")
