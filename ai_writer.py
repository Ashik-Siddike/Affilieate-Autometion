import google.generativeai as genai
from config import GEMINI_API_KEYS
import time

# API Key Rotation System (Similar to ScrapingAnt)
_current_key_index = 0  # Track current API key index

def get_current_gemini_key():
    """Returns the current Gemini API key."""
    if not GEMINI_API_KEYS:
        raise ValueError("No Gemini API keys configured in config.py")
    return GEMINI_API_KEYS[_current_key_index]

def switch_to_next_gemini_key():
    """Switches to the next Gemini API key in rotation."""
    global _current_key_index
    _current_key_index = (_current_key_index + 1) % len(GEMINI_API_KEYS)
    print(f"🔄 Switched to Gemini API key {_current_key_index + 1}/{len(GEMINI_API_KEYS)}")

def is_quota_error(error):
    """
    Checks if the error indicates quota/credit exhaustion.
    Returns True if we should switch to next API key.
    """
    error_str = str(error).lower()
    quota_indicators = [
        "429",
        "quota exceeded",
        "quota",
        "resource exhausted",
        "rate limit",
        "permission denied",
        "403",
        "billing",
        "credit"
    ]
    return any(indicator in error_str for indicator in quota_indicators)

def get_gemini_model(api_key):
    """Creates and returns a Gemini model instance with the given API key."""
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-flash-latest')

def generate_article(product_data, similar_products=None, internal_links=None):
    """
    Generates a High-Quality, E-E-A-T focused, SEO-friendly article.
    Includes retry logic for 429 Quota Exceeded errors.
    """
    if not product_data:
        return None

    title = product_data.get('title', 'Unknown Product')
    price = product_data.get('price', 'N/A')
    rating = product_data.get('rating', 'N/A')
    review_count = product_data.get('review_count', '0')
    product_link = product_data.get('product_url', '#')
    
    # Construct Comparison Data
    comparison_text = ""
    if similar_products:
        comparison_text = "### Comparison Table Data (Use this to build the HTML table):\n"
        for p in similar_products:
            comparison_text += f"- Compare with: {p.get('title')} | Price: {p.get('price')} | Rating: {p.get('rating')}\n"
    
    # Construct Internal Links Data
    links_text = ""
    if internal_links:
        links_text = "### Internal Links to Mention (Contextually insert these links where relevant in the text):\n"
        for p in internal_links:
            links_text += f"- Link Text: '{p.get('title')}' -> URL: {p.get('link')}\n"

    # ======================================================
    # THE ULTIMATE SEO PROMPT (Human-Like & Deep)
    # ======================================================
    prompt = f"""
    Act as a Senior Tech Reviewer with 10 years of experience. Write a deep, honest, and SEO-optimized product review for the following product.

    ### Product Data:
    - Name: {title}
    - Price: {price}
    - Rating: {rating} stars
    - Review Count: {review_count} reviews
    
    {comparison_text}
    {links_text}

    ### Writing Guidelines (Strictly Follow):
    1. **Tone:** Conversational, professional, unbiased, and empathetic. Use "I", "We", and "You". Avoid robotic AI words like "unleash", "game-changer", "realm", "delve", "landscape".
    2. **Formatting:** Use proper HTML tags (<h2>, <h3>, <p>, <ul>, <li>, <table>, <strong>). Ensure ALL tags are properly closed.
    3. **Structure:** Short paragraphs (2-3 lines max). Use bullet points for readability.
    4. **SEO:** Include the product name naturally in the first 100 words.
    5. **Affiliate Link:** You MUST include a "Check Price on Amazon" button using the URL: {product_link}
    6. **Comparison Table:** If comparison data is provided, create a responsive HTML table comparing the main product with the others.
    7. **Internal Linking:** If internal links are provided, insert them NATURALLY within the content (e.g. "If you are looking for X, check out our review of [Link]"). Do not list them at the end.

    ### Article Structure (Output only the HTML body):
    
    <p><strong>Verdict at a Glance:</strong> <em>Write a 2-sentence summary here for busy readers. Is it a buy or pass?</em></p>

    <!-- Buy Button -->
    <div style="text-align: center; margin: 20px 0;">
        <a href="{product_link}" target="_blank" rel="nofollow sponsored" style="background-color: #FF9900; color: black; padding: 15px 30px; text-decoration: none; font-weight: bold; font-size: 18px; border-radius: 5px; border: 1px solid #b36b00;">Check Price on Amazon</a>
    </div>

    <h2>Introduction</h2>
    <p>Hook the reader with a relatable problem this product solves. Mention the price point and who it is mainly for.</p>

    <!-- COMPARISON TABLE HERE IF DATA EXISTS -->

    <h2>Key Features & Real-World Performance</h2>
    <p>Don't just list specs. Explain the *benefit* of each feature. Use <h3> subheadings for major features.</p>
    <ul>
        <li><strong>Feature 1:</strong> Explain why it matters.</li>
        <li><strong>Feature 2:</strong> Explain the real-world usage.</li>
    </ul>

    <h2>Pros and Cons</h2>
    <p>Be honest. A review without cons looks fake.</p>
    <table border="0" style="width: 100%; border-collapse: collapse; margin: 20px 0; font-family: Arial, sans-serif;">
        <thead>
            <tr>
                <th style="width: 50%; padding: 12px; background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; text-align: left;">✅ Pros</th>
                <th style="width: 50%; padding: 12px; background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; text-align: left;">❌ Cons</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td style="vertical-align: top; padding: 10px; border: 1px solid #c3e6cb; background-color: #ffff;">
                    <ul style="margin: 0; padding-left: 20px;">
                        <li>List pro 1</li>
                        <li>List pro 2</li>
                    </ul>
                </td>
                <td style="vertical-align: top; padding: 10px; border: 1px solid #f5c6cb; background-color: #ffff;">
                    <ul style="margin: 0; padding-left: 20px;">
                        <li>List con 1</li>
                        <li>List con 2</li>
                    </ul>
                </td>
            </tr>
        </tbody>
    </table>

    <!-- Buy Button Again -->
    <div style="text-align: center; margin: 20px 0;">
        <a href="{product_link}" target="_blank" rel="nofollow sponsored" style="background-color: #FF9900; color: black; padding: 15px 30px; text-decoration: none; font-weight: bold; font-size: 18px; border-radius: 5px; border: 1px solid #b36b00;">Check Price on Amazon</a>
    </div>

    <h2>Who Should Buy This?</h2>
    <p>Clearly define the user persona (e.g., "Best for budget gamers" or "Perfect for busy moms").</p>

    <h2>Final Verdict</h2>
    <p>Give a clear recommendation. Rate it out of 10 based on value for money.</p>

    <h2>Frequently Asked Questions (FAQ)</h2>
    <p>Add 3 common questions people might ask about this type of product.</p>
    
    ### Output Rule:
    Return ONLY the raw HTML code. Do NOT wrap it in markdown block (```html).
    """

    # API Key Rotation System: Try all keys if quota errors occur
    if not GEMINI_API_KEYS:
        print("❌ No Gemini API keys configured. Please add keys in config.py")
        return None
    
    keys_tried = set()  # Track which keys we've already tried for this request
    
    for key_attempt in range(len(GEMINI_API_KEYS)):
        current_key = get_current_gemini_key()
        key_id = f"{current_key[:10]}..."  # Show partial key for logging
        
        # Skip if we've already tried this key (shouldn't happen, but safety check)
        if current_key in keys_tried:
            switch_to_next_gemini_key()
            continue
            
        keys_tried.add(current_key)
        print(f"🤖 Using Gemini API key {_current_key_index + 1}/{len(GEMINI_API_KEYS)} ({key_id})")
        
        try:
            # Create model with current API key
            model = get_gemini_model(current_key)
            print(f"📝 Writing article for '{title}'...")
            
            response = model.generate_content(prompt)
            
            if response and response.text:
                clean_text = response.text.replace("```html", "").replace("```", "").strip()
                print(f"✅ Article generated successfully with key {_current_key_index + 1}")
                return clean_text
            else:
                print("⚠️ Gemini returned empty response. Trying next key...")
                switch_to_next_gemini_key()
                time.sleep(2)  # Brief pause before switching keys
                continue

        except Exception as e:
            error_str = str(e)
            
            # Check if it's a quota/credit exhaustion error
            if is_quota_error(e):
                print(f"⚠️ Quota/Credit exhausted on key {_current_key_index + 1} ({key_id})")
                print(f"   Error: {error_str[:200]}...")
                
                # Switch to next key
                if key_attempt < len(GEMINI_API_KEYS) - 1:
                    switch_to_next_gemini_key()
                    time.sleep(2)  # Brief pause before trying next key
                    continue
                else:
                    print(f"❌ All {len(GEMINI_API_KEYS)} API keys exhausted. Please add more keys or wait for quota reset.")
                    return None
            else:
                # For non-quota errors, log and retry with same key (with delay)
                print(f"⚠️ Error with key {_current_key_index + 1}: {error_str[:200]}...")
                print(f"   Retrying with same key after delay...")
                time.sleep(5)
                
                try:
                    model = get_gemini_model(current_key)
                    response = model.generate_content(prompt)
                    if response and response.text:
                        clean_text = response.text.replace("```html", "").replace("```", "").strip()
                        return clean_text
                except Exception as retry_error:
                    # If retry also fails, try next key
                    if is_quota_error(retry_error):
                        if key_attempt < len(GEMINI_API_KEYS) - 1:
                            switch_to_next_gemini_key()
                            continue
                    print(f"❌ Retry failed: {retry_error}")
    
    print(f"❌ Failed to generate article after trying all {len(GEMINI_API_KEYS)} API keys")
    return None