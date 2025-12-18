import json
import datetime

def generate_product_schema(product_data, article_url=None):
    """
    Generates JSON-LD schema for a product review.
    
    Args:
        product_data (dict): Dictionary containing product details (title, price, rating, etc.)
        article_url (str, optional): The URL where this review will be published.
    
    Returns:
        str: A string containing the <script type="application/ld+json"> block.
    """
    if not product_data:
        return ""

    title = product_data.get('title', 'Unknown Product')
    image = product_data.get('image_url', '')
    description = f"Review of {title}" # Simple description
    sku = product_data.get('asin', '')
    
    # Price handling - remove currency symbols if present for 'price' field validation usually
    # But schema.org accepts text price often, but numeric is better.
    # The scraper returns price as string likely with $. 
    # Let's keep it simple for now or strip.
    price_raw = product_data.get('price', '0')
    price = price_raw.replace('$', '').replace(',', '')
    try:
        float(price)
    except ValueError:
        price = "0"

    rating_value = product_data.get('rating', '0').split(' ')[0] # "4.5 out of 5" -> "4.5"
    review_count = product_data.get('review_count', '0').replace(',', '')

    schema = {
        "@context": "https://schema.org/",
        "@type": "Product",
        "name": title,
        "image": image,
        "description": description,
        "sku": sku,
        "brand": {
            "@type": "Brand",
            "name": "Unknown" # Scraper doesn't get brand yet, placeholder
        },
        "offers": {
            "@type": "Offer",
            "url": product_data.get('product_url', ''),
            "priceCurrency": "USD",
            "price": price,
            "availability": "https://schema.org/InStock"
        },
        "aggregateRating": {
            "@type": "AggregateRating",
            "ratingValue": rating_value,
            "reviewCount": review_count
        },
        "review": {
            "@type": "Review",
            "reviewRating": {
              "@type": "Rating",
              "ratingValue": "5", # Our review is always positive? Or we can use the product rating
              "bestRating": "5"
            },
            "author": {
              "@type": "Person",
              "name": "AI Reviewer"
            },
            "datePublished": datetime.date.today().isoformat()
        }
    }

    return f'<script type="application/ld+json">\n{json.dumps(schema, indent=4)}\n</script>'
