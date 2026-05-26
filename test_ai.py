import ai_writer
import schema_helper
import sys
from config import GEMINI_API_KEYS

# Ensure UTF-8 output on Windows terminal
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

print(f"Loaded keys: {len(GEMINI_API_KEYS)}")
product_data = {"asin": "B0TEST1234", "title": "SKMEI Waterproof Military Watch", "price": "$19.99", "rating": "4.5 out of 5 stars", "review_count": "150", "product_url": "https://www.amazon.com/dp/B0TEST1234"}

content, social = ai_writer.generate_article(
    product_data, 
    similar_products=None, 
    internal_links=None, 
    language="English", 
    competitor_text=None
)

print("=" * 60)
print("Content generated successfully:")
print("=" * 60)
print(content[:500] + "...")
print("=" * 60)
print("Social & Metadata block:")
print("=" * 60)
print(social)

print("=" * 60)
print("Generated Schema Script:")
print("=" * 60)
brand_name = product_data.get('title', '').split(' ')[0]
pros = social.get('pros') if isinstance(social, dict) else None
cons = social.get('cons') if isinstance(social, dict) else None

schema_script = schema_helper.generate_product_schema(
    product_data,
    faqs=None,
    brand_name=brand_name,
    pros=pros,
    cons=cons
)
print(schema_script)
print("=" * 60)
