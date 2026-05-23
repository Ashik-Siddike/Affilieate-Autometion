import json
import datetime

def generate_product_schema(product_data, article_url=None, faqs=None):
    """
    Generates JSON-LD schema for a product review and FAQ.
    
    Args:
        product_data (dict): Dictionary containing product details (title, price, rating, etc.)
        article_url (str, optional): The URL where this review will be published.
        faqs (list, optional): List of dicts with 'question' and 'answer' keys.
    
    Returns:
        str: A string containing the <script type="application/ld+json"> blocks.
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
              "ratingValue": rating_value if float(rating_value) > 0 else "5",
              "bestRating": "5"
            },
            "author": {
              "@type": "Person",
              "name": "Expert Reviewer"
            },
            "datePublished": datetime.date.today().isoformat(),
            "positiveNotes": {
              "@type": "ItemList",
              "itemListElement": [
                {
                  "@type": "ListItem",
                  "position": 1,
                  "name": "Excellent build quality and durability"
                },
                {
                  "@type": "ListItem",
                  "position": 2,
                  "name": "Great value for the price point"
                }
              ]
            },
            "negativeNotes": {
              "@type": "ItemList",
              "itemListElement": [
                {
                  "@type": "ListItem",
                  "position": 1,
                  "name": "Availability might be limited occasionally"
                }
              ]
            }
        }
    }

    schema_blocks = [f'<script type="application/ld+json">\n{json.dumps(schema, indent=4)}\n</script>']
    
    # ── FAQ Schema ──
    if faqs and isinstance(faqs, list) and len(faqs) > 0:
        faq_schema = {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": []
        }
        for faq in faqs:
            if isinstance(faq, dict) and faq.get('question') and faq.get('answer'):
                faq_schema["mainEntity"].append({
                    "@type": "Question",
                    "name": faq['question'],
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": faq['answer']
                    }
                })
        schema_blocks.append(f'<script type="application/ld+json">\n{json.dumps(faq_schema, indent=4)}\n</script>')

    return "\n\n".join(schema_blocks)
