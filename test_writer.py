from ai_writer import generate_article

mock_product = {
    'title': 'Test Product',
    'price': '$19.99',
    'rating': '4.5',
    'review_count': '100',
    'product_url': 'https://example.com'
}

print("Running test generation...")
result = generate_article(mock_product)
if result:
    print("Test passed! Article generated.")
    print(result[:100] + "...")
else:
    print("Test failed.")
