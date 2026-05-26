from config import GEMINI_API_KEYS, SCRAPINGANT_API_KEYS
import time
try:
    from youtubesearchpython import VideosSearch
except ImportError:
    VideosSearch = None
import random
import requests
import re
import json
from google import genai

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
    print(f" Switched to Gemini API key {_current_key_index + 1}/{len(GEMINI_API_KEYS)}")

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
    return genai.Client(api_key=api_key)

def find_review_video(product_name):
    """Searches YouTube for a review video and returns an embed code."""
    if VideosSearch is not None:
        try:
            query = f"{product_name} review"
            # Search for 1 video
            videosSearch = VideosSearch(query, limit = 1)
            results = videosSearch.result()
            
            if results['result']:
                video = results['result'][0]
                video_id = video['id']
                title = video['title']
                
                # Create Responsive Embed Code
                embed_code = f'''
                <div class="video-wrapper" style="margin: 30px 0; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
                    <h3 style="margin-bottom: 15px; font-size: 1.2rem;">📺 Watch: {title}</h3>
                    <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden;">
                        <iframe style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; border:0;" 
                            src="https://www.youtube.com/embed/{video_id}" 
                            title="{title}" 
                            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                            allowfullscreen>
                        </iframe>
                    </div>
                </div>
                '''
                return embed_code
        except Exception as e:
            print(f" Primary Video Search Failed: {e}")
            pass

    # --- FALLBACK: ScrapingAnt Search ---
    print(" Attempting Fallback Video Search via ScrapingAnt...")
    search_url = f"https://www.youtube.com/results?search_query={product_name.replace(' ', '+')}+review"
    
    for api_key in SCRAPINGANT_API_KEYS:
        try:
             response = requests.get(
                "https://api.scrapingant.com/v2/general",
                params={'url': search_url, 'browser': 'false'}, # youtube results usually minimal js needed for first hit? or true? use true to be safe
                headers={'x-api-key': api_key},
                timeout=40
            )
             if response.status_code == 200:
                 html = response.text
                 # Find video ID: /watch?v=VIDEO_ID
                 # Regex for video ID (11 chars)
                 match = re.search(r'/watch\?v=([a-zA-Z0-9_-]{11})', html)
                 if match:
                     video_id = match.group(1)
                     title = f"{product_name} Review" # Fallback title
                     embed_code = f'''
                    <div class="video-wrapper" style="margin: 30px 0; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
                        <h3 style="margin-bottom: 15px; font-size: 1.2rem;">📺 Watch: {title}</h3>
                        <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden;">
                            <iframe style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; border:0;" 
                                src="https://www.youtube.com/embed/{video_id}" 
                                title="{title}" 
                                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                                allowfullscreen>
                            </iframe>
                        </div>
                    </div>
                    '''
                     print(" Fallback Video Found!")
                     return embed_code
        except Exception as e:
            print(f"Fallback key failed: {e}")
            continue
            
    return ""

def generate_article(product_data, similar_products=None, internal_links=None, language='English', competitor_text=None, affiliate_tag=None, niche_prompt=None):
    """
    Generates a Human-Like, GEO (Generative Engine Optimized) article.
    """
    if not product_data:
        return None, None

    title = product_data.get('title', 'Unknown Product')
    price = product_data.get('price', 'N/A')
    rating = product_data.get('rating', 'N/A')
    review_count = product_data.get('review_count', '0')
    product_link = product_data.get('product_url', '#')
    
    # Construct Context Data
    comparison_text = ""
    if similar_products and isinstance(similar_products, list):
        comparison_text = "### 📊 Comparison Data:\n"
        for p in similar_products:
            if isinstance(p, dict):
                comparison_text += f"- Compare with: {p.get('title', 'Unknown')} | Price: {p.get('price', 'N/A')} | Rating: {p.get('rating', 'N/A')}\n"
    
    links_text = ""
    if internal_links and isinstance(internal_links, list):
        links_text = "### 🔗 INTERNAL LINKING INSTRUCTION (CRITICAL):\n"
        links_text += "I am providing you with previously published articles from our site. You MUST naturally weave 1 or 2 of these links into the body paragraphs of your article using contextual HTML anchor tags (e.g. <a href=\"...\">anchor text</a>). Do NOT just list them at the end. Integrate them smoothly as helpful resources.\n\n"
        for p in internal_links:
            if isinstance(p, dict):
                links_text += f"- Target URL: {p.get('link', '#')} (Context/Topic: {p.get('title', 'Link')})\n"

    # --- 🎥 VIDEO SEARCH ---
    video_embed_code = find_review_video(title)
    video_instruction = ""
    if video_embed_code:
        video_instruction = f"""
        **🎥 VIDEO EMBEDDING INSTRUCTION:**
        I have found a relevant YouTube review video.
        PLEASE INSERT the following exact HTML code block right before the 'Final Conclusion' section:
        
        {video_embed_code}
        
        Do not alter the HTML code. Just place it where requested.
        """

    # --- SKYSCRAPER MODE ---
    skyscraper_instruction = ""
    if competitor_text:
        skyscraper_instruction = f"""
        ### 🕵️ COMPETITOR INTELLIGENCE (SKYSCRAPER MODE)
        I have analyzed a top-ranking competitor's article for this topic.
        Here is their content (Reference Only):
        {competitor_text[:3000]}... (Truncated)

        **YOUR MISSION (SKYSCRAPER TECHNIQUE):**
        1. OUTRANK this content. Write an article that is DEEPER, More Helpful, and Better Structured.
        2. Identify points they missed and include them.
        3. Do NOT copy their text. Use it as a quality benchmark to beat.
        """

    # ======================================================
    # 🧠 SYSTEM INSTRUCTION (Identity & Style)
    # ======================================================
    system_instruction = """
    You are an Expert Product Tester & Consumer Advocate. 
    Your goal is to write a review that feels 100% human, honest, and personal.
    
    🌍 **LANGUAGE REQUIREMENT:**
    You MUST write the ENTIRE ARTICLE in **{language}**.
    - All headings, paragraphs, and lists must be in **{language}**.
    - Do NOT mix languages unless referencing the product name itself.
    
    ❌ **FORBIDDEN AI WORDS (Never use these):**
    - Unleash, Unlock, Realm, Landscape, Tapestry, Symphony, Game-changer, Delve, Dive deep, Bustling, Vibrant, Meticulous, Paramount, Elevate.
    
    ✅ **TONE & STYLE (Must follow):**
    - **Conversational:** Write like you are talking to a friend. Use "I", "We", "You".
    - **Direct:** Don't fluff. Get to the point.
    - **Varied Syntax:** Mix short punchy sentences with longer descriptive ones. (Perplexity/Burstiness).
    - **Experience:** Simulate real experience. Say "I felt..." or "In my testing...".
    """

    # ── Inject Amazon Affiliate Tag into CTA link ──
    if not affiliate_tag:
        from config import AMAZON_AFFILIATE_TAG
        affiliate_tag = AMAZON_AFFILIATE_TAG

    if affiliate_tag and product_link and product_link != '#':
        sep = '&' if '?' in product_link else '?'
        product_link_with_tag = f"{product_link}{sep}tag={affiliate_tag}"
    else:
        product_link_with_tag = product_link

    # ── Article Variety: 33% chance of Top 10, 67% standard review ──
    article_type = random.choice(["review", "review", "top10"])

    # ======================================================
    # 📝 USER PROMPT (Structure & Content)
    # ======================================================
    if article_type == "top10":
        keyword_words = title.split()[:3]
        list_topic = " ".join(keyword_words)
        prompt = f"""
    Write a complete, HTML-formatted "Top 10 Best {list_topic}" list article in **{language}** language.
    Use this product as the #1 recommendation: **{title}** (Price: {price}, Rating: {rating} stars)

    {skyscraper_instruction}
    {comparison_text}
    {links_text}

    ### STRUCTURE:
    {video_instruction}

    1. `<h1>Top 10 Best {list_topic} in 2025</h1>` + 150-word intro
    2. Quick Comparison Table (HTML): Rank | Product | Price | Rating | Best For
       — Feature our product as #1, add 4 generic placeholders (#2-#5)
    3. #1 Full review of **{title}** (200 words)
    4. #2-#5: 50-word placeholders each
    5. FAQ: 3 questions
    6. Final Verdict + CTA button:
    <div style="text-align: center; margin: 30px 0;">
        <a href="{product_link_with_tag}" target="_blank" rel="nofollow sponsored" data-amz-cta="true"
           style="display:inline-block; background: linear-gradient(180deg, #f8e1aa 0%, #f4d078 100%); color: #111; padding: 14px 28px; border-radius: 8px; font-weight: bold; font-size: 1.1rem; text-decoration: none; border: 1px solid #a88734; box-shadow: 0 2px 5px rgba(0,0,0,0.1); cursor: pointer;">
           🛒 Check #1 Pick Price on Amazon
        </a>
    </div>

    Output raw HTML body only.

    ```json
    {{
      "fb_content": "🔥 TOP 10 {list_topic} RANKED!\\n\\nI've tested dozens. Here's my honest #1 pick: {title}\\n\\n👇 Full list: [post_link]\\n\\n#BestOf2025 #Shopping",
      "pin_title": "Top 10 Best {list_topic} 2025 — Expert Ranked",
      "pin_desc": "Looking for the best {list_topic}? We tested 10 options. {title} is our #1 pick. Save this for later! 🛒",
      "ig_content": "✨ 10 best {list_topic} — ranked by testing!\\n\\n#1: {title}\\n\\n🔗 Full breakdown in bio link!\\n\\n#TopPick #ProductReview #BestOf2025"
    }}
    ```
    """
    else:
        prompt = f"""
    Write a complete, HTML-formatted product review for: **{title}**
    in **{language}** language.
    
    {skyscraper_instruction}
    
    **Product Info:**
    - Price: {price} | Rating: {rating} stars ({review_count} reviews)
    
    {comparison_text}
    {links_text}

    ### 🧱 STRICT OUTPUT STRUCTURE (HTML BODY ONLY) 🧱
    
    {video_instruction}

    **1. ⚡ Quick Verdict (Featured Snippet Bait)**
    - Start with an `<h2>Quick Verdict</h2>`.
    - Provide a direct "Yes/No" recommendation in bold.
    - Write a 40-50 word summary answering "Is it worth buying?".

    **2. 🔑 Key Takeaways**
    - `<h2>Key Takeaways</h2>`
    - A bulleted list of the top 3-4 most important pros/facts.

    **3. 📦 Introduction**
    - Personal hook. Why does this product exist? Who needs it?

    **4. 🛠️ Build & Design (or relevant feature)**
    - Use `<h2>` and `<h3>`. Talk about quality and feel.

    **5. 🏆 Performance / In-Depth Testing**
    - Detailed analysis. Mention specific features.

    **6. 🆚 Comparison (If data provided)**
    - Create a responsive HTML table.

    **7. ✅ Pros & ❌ Cons**
    - Use a styled HTML table (Green for Pros, Red for Cons).

    **8. ❓ FAQ (Voice Search Optimization)**
    - `<h2>FAQ</h2>`
    - Include 3 common questions people might ask about this specific type of product.
    - Answer them concisely (good for Google "People Also Ask").

    **9. 🎯 Final Conclusion**
    - Who exactly should buy this? (Persona based).

    **CTA Requirements:**
    - Use this exact Amazon link with affiliate tag: {product_link_with_tag}
    - Insert a "Check Price on Amazon" button after the Intro and at the very end:
    <div style="text-align: center; margin: 30px 0;">
        <a href="{product_link_with_tag}" target="_blank" rel="nofollow sponsored" data-amz-cta="true"
           style="display:inline-block; background: linear-gradient(180deg, #f8e1aa 0%, #f4d078 100%); color: #111; padding: 14px 28px; border-radius: 8px; font-weight: bold; font-size: 1.1rem; text-decoration: none; border: 1px solid #a88734; box-shadow: 0 2px 5px rgba(0,0,0,0.1); cursor: pointer;">
           🛒 Check Latest Price on Amazon
        </a>
    </div>

    
    **Formatting:**
    - Output raw HTML body only (no ```html tags).
    - Use <h2>, <h3>, <p>, <ul>, <li>, <strong>.

    **10. 📢 Premium Social Media Bundle (JSON)**
    - At the VERY END, generate a strictly valid JSON block.
    - Write the social media copy with the SAME intelligence, depth, and human-like quality as the main article.
    - Use advanced copywriting frameworks (AIDA, PAS). Act like a top-tier social media influencer and conversion copywriter.
    - Format exactly like this:
    ```json
    {{
      "fb_content": "🔥 [ATTENTION HOOK]\nStart with a highly relatable, contrarian, or thought-provoking statement that stops the scroll.\n\n💬 [BRIDGE/STORY]\nWrite 2-3 short, punchy paragraphs explaining the core problem and how this product is the ultimate solution. Be authentic, engaging, and smart. Use spacing for readability.\n\n👇 [CALL TO ACTION]\nGive them a clear, irresistible reason to click the link right now.\n\n#HighlyRelevant1 #HighlyRelevant2",
      "pin_title": "Catchy SEO Title for Pinterest (Max 90 chars)",
      "pin_desc": "Keyword-rich description highlighting the main benefit. Use bullet points. End with strong CTA: 'Save this pin & check the link to grab yours today!' #TargetKeyword1 #TargetKeyword2",
      "ig_content": "✨ [STORYTELLING HOOK]\nStart with an engaging micro-story or a bold statement about a lifestyle upgrade.\n\n[VALUE DRIVEN BODY]\nBreak down WHY this product changes the game using bullet points or short, aesthetic paragraphs. Speak directly to their desires and pain points. Keep it visually structured.\n\n🔗 [BIO CTA]\nTell them exactly what to do next: 'Click the LINK IN BIO to check out the {title} and upgrade your setup!'\n\n#NicheHashtag1 #NicheHashtag2 (15-20 highly targeted hashtags)",
      "x_content": "🚨 Don't miss out on the {title}! The ultimate solution for [Main Benefit]. \n\nCheck out why we recommend it 👇\n{product_link} \n\n#Hashtag1 #Hashtag2"
    }}
    ```
    - Ensure this JSON is strictly valid, properly quoted, and completely separated from the HTML above it.
    """

    api_key = get_current_gemini_key()
    
    # Retry Logic for Quota (Try all keys if needed)
    max_attempts = len(GEMINI_API_KEYS) * 2

    for attempt in range(max_attempts):
        current_key = get_current_gemini_key()
        
        try:
            final_prompt = system_instruction + "\n\n" + prompt
            client = genai.Client(api_key=current_key)
            
            response   = None
            last_error = None
            
            # --- Try preferred models in order ---
            preferred_models = [
                'gemini-2.5-flash',
                'gemini-1.5-flash',
                'gemini-1.5-pro',
                'gemini-1.0-pro',
                'gemini-pro',
            ]
            
            FLUFF_WORDS   = ["unleash", "unlock", "realm", "landscape", "tapestry",
                             "symphony", "game-changer", "delve", "dive deep",
                             "bustling", "vibrant", "meticulous", "paramount", "elevate"]
            MAX_FLUFF_RETRIES = 3

            for model_name in preferred_models:
                try:
                    # Fluff-check validation loop
                    for fluff_attempt in range(MAX_FLUFF_RETRIES):
                        r = client.models.generate_content(
                            model=model_name,
                            contents=final_prompt
                        )
                        if r and r.text:
                            found_fluff = [w for w in FLUFF_WORDS if w in r.text.lower()]
                            if not found_fluff:
                                print(f"[AI] Model: {model_name} | Fluff check passed (attempt {fluff_attempt+1})")
                                response = r
                                break
                            else:
                                print(f"[AI] Fluff detected: {found_fluff}. Retry {fluff_attempt+1}/{MAX_FLUFF_RETRIES}...")
                                if fluff_attempt == MAX_FLUFF_RETRIES - 1:
                                    print(f"[AI] Fluff retry limit hit for {model_name}. Accepting anyway.")
                                    response = r
                        else:
                            break

                    if response:
                        break  # Got a valid response — stop trying other models

                except Exception as model_err:
                    if is_quota_error(model_err):
                        raise model_err  # Let outer loop handle key rotation
                    if "404" in str(model_err) or "not found" in str(model_err).lower():
                        continue       # Model not available — try next
                    last_error = model_err
                    continue

            # --- Fallback: auto-discover available models ---
            if not response:
                print("[AI] Standard models failed. Auto-discovering available models...")
                try:
                    all_models   = list(client.models.list())
                    valid_models = [m.name for m in all_models if hasattr(m, 'supported_generation_methods') and 'generateContent' in m.supported_generation_methods or 'gemini' in m.name.lower()]
                    if valid_models:
                        best_model = next((m for m in valid_models if 'flash' in m), valid_models[0])
                        print(f"[AI] Auto-selected: {best_model}")
                        response = client.models.generate_content(
                            model=best_model,
                            contents=final_prompt
                        )
                    else:
                        print("[AI] No valid models found on this key.")
                        if last_error:
                            raise last_error
                except Exception as disc_err:
                    raise disc_err

            # --- Parse and return successful response ---
            if response and response.text:
                content     = response.text
                social_data = {}

                # ── Strategy 1: ```json ... ``` fenced block ──
                json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
                if json_match:
                    try:
                        social_data = json.loads(json_match.group(1))
                        content = content.replace(json_match.group(0), "").strip()
                    except Exception:
                        content = content.replace(json_match.group(0), "").strip()

                # ── Strategy 2: bare JSON object at the end ──
                if not social_data:
                    bare_match = re.search(
                        r'(\{\s*"fb_content"\s*:.*?\})\s*$',
                        content, re.DOTALL
                    )
                    if bare_match:
                        try:
                            social_data = json.loads(bare_match.group(1))
                            content = content.replace(bare_match.group(0), "").strip()
                        except Exception:
                            content = content.replace(bare_match.group(0), "").strip()

                # ── Strategy 3: any JSON block with social keys ──
                if not social_data:
                    any_json = re.search(
                        r'(\{[^{}]*"(?:fb_content|pin_title|ig_content|x_content)"[^{}]*\})',
                        content, re.DOTALL
                    )
                    if any_json:
                        try:
                            social_data = json.loads(any_json.group(1))
                        except Exception:
                            pass
                        content = content[:any_json.start()].strip()

                # ── Aggressive fallback: strip anything from first { with social keys ──
                for key in ['"fb_content"', '"pin_title"', '"ig_content"', '"x_content"']:
                    idx = content.find(key)
                    if idx != -1:
                        # Walk back to find opening {
                        brace_pos = content.rfind('{', 0, idx)
                        if brace_pos != -1:
                            content = content[:brace_pos].strip()
                        break

                # ── Strip markdown code fences ──
                content = re.sub(r'```(?:html|json)?\s*', '', content)
                content = re.sub(r'```\s*', '', content)
                content = content.strip('`').strip()

                return content, social_data


            # If we get here, no response was obtained
            print(f"[AI] Attempt {attempt+1}: No response obtained.")
            if last_error:
                raise last_error

        except Exception as e:
            if is_quota_error(e):
                print(f"[AI] Quota exceeded. Switching API key...")
                switch_to_next_gemini_key()
                time.sleep(2)
            else:
                print(f"[AI] Error on attempt {attempt+1}: {e}")
                switch_to_next_gemini_key()

    print("[AI] All API keys and retries exhausted. Returning None.")
    return None, None


def generate_social_captions(title: str, brand: str, amazon_url: str, review_url: str, niche_prompt: str = None) -> dict:
    """
    Uses Gemini to generate highly-optimized, platform-specific social media captions.
    Returns a dict with keys: fb_content, ig_content, pin_title, pin_desc, linkedin_content
    """
    FALLBACK = {
        "fb_content": f"🔥 {title}\n\n💰 Best price on Amazon!\n✅ Full Review → {review_url}\n\n#ProductReview #Amazon #BestDeals",
        "ig_content": f"🔥 {title}\n\n💰 Best price on Amazon!\n✅ Full review — link in bio\n\n#ProductReview #Amazon #BestDeals #Shopping #AffiliateMarketing #MustHave",
        "pin_title": f"{title} - Expert Review",
        "pin_desc": f"{title} — Full Review & Best Price on Amazon! Click to read the complete review! {review_url}\n\n#ProductReview #Amazon #BestDeals #Shopping",
        "linkedin_content": f"🔎 Just published a detailed review of the {brand} — {title}\n\nGreat value for money! Check it out → {review_url}\n\n#ProductReview #Amazon #Deals",
    }
    
    niche_desc = f"reviewing {niche_prompt}" if niche_prompt else "reviewing best products and gear"

    prompt = f"""You are an expert social media copywriter for "Whit Logic", an affiliate blog {niche_desc}.

Generate platform-optimized social media content for this product:
Product: {title}
Brand: {brand}
Amazon Link: {amazon_url}
Review Link: {review_url}

Return ONLY a valid JSON object (no markdown, no extra text) with these exact keys:
{{
  "fb_content": "Conversational, engaging Facebook post. 2-3 short paragraphs. Include emojis. End with CTA to click the review link. Include 3-5 relevant hashtags.",
  "ig_content": "Visual, emoji-rich Instagram caption with line breaks. 15-20 hashtags. End with 'Link in bio!'. Do NOT include the actual URL.",
  "pin_title": "SEO-friendly Pinterest pin title under 100 characters. Focus on value/benefit.",
  "pin_desc": "Pinterest description under 500 characters. Include the review URL naturally. Add 5-8 hashtags.",
  "linkedin_content": "Professional, value-driven LinkedIn post. 2-3 paragraphs. Focus on value-for-money. Include review URL. 3-5 professional hashtags."
}}"""

    max_attempts = len(GEMINI_API_KEYS) * 2
    for attempt in range(max_attempts):
        try:
            api_key = get_current_gemini_key()
            client = get_gemini_model(api_key)
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
            )
            raw = response.text.strip()
            raw = re.sub(r'```(?:json)?\s*', '', raw)
            raw = re.sub(r'```\s*', '', raw).strip()

            start = raw.find('{')
            end = raw.rfind('}') + 1
            if start == -1 or end == 0:
                raise ValueError("No JSON found in response.")

            captions = json.loads(raw[start:end])
            for key in FALLBACK:
                if key not in captions or not captions[key]:
                    captions[key] = FALLBACK[key]

            print("[AI] ✅ Platform-specific social captions generated.")
            return captions

        except Exception as e:
            if is_quota_error(e):
                print(f"[AI:social] Quota exceeded (attempt {attempt+1}). Switching key...")
                switch_to_next_gemini_key()
                time.sleep(2)
            else:
                print(f"[AI:social] Error (attempt {attempt+1}): {e}. Switching key...")
                switch_to_next_gemini_key()
                time.sleep(1)

    print("[AI:social] All retries exhausted. Using fallback captions.")
    return FALLBACK


def generate_faqs(title: str, brand: str, model_number: str, niche_prompt: str = None) -> list:
    """
    Uses Gemini to generate 6 SEO-optimized FAQ pairs for a product review.
    Returns a list of {"question": ..., "answer": ...} dicts.
    Targets Google's "People Also Ask" rich snippets.
    """
    FALLBACK = [
        {"question": f"Is the {brand} {model_number} worth buying?", "answer": f"Yes, the {brand} {model_number} offers excellent value for money. It combines durability, style, and functionality at an affordable price point, making it a top choice for budget-conscious buyers."},
        {"question": f"What are the best features of the {brand} {model_number}?", "answer": f"The {brand} {model_number} comes with excellent build quality and reliable performance. We recommend checking the specific features in our full review above for exact specifications."},
        {"question": f"How long does the {brand} {model_number} last?", "answer": f"Lifespan varies by usage. In standard mode, the {brand} {model_number} offers excellent long-term performance. Refer to the specs table in our review for exact details."},
        {"question": f"Where can I buy the {brand} {model_number} at the best price?", "answer": f"The best price for the {brand} {model_number} is usually found on Amazon. We recommend checking our affiliate link above for the latest pricing and any available discounts."},
        {"question": f"What is the warranty on the {brand} {model_number}?", "answer": f"Warranty terms vary by seller. We recommend purchasing from Amazon's fulfilled listings for the best buyer protection and return policy."},
        {"question": f"How does the {brand} {model_number} compare to competitors?", "answer": f"The {brand} {model_number} stands out from competitors in its price range by offering a combination of durability, features, and brand reliability. See our detailed comparison in the review above."},
    ]
    
    niche_desc = f"that focuses on {niche_prompt}" if niche_prompt else "that focuses on high quality products"

    prompt = f"""You are an SEO expert writing FAQ content for a product review blog called "Whit Logic" {niche_desc}.

Generate exactly 6 FAQ question-and-answer pairs for this product:
Product Name: {title}
Brand: {brand}
Model: {model_number}

Rules:
- Questions must be what real customers search on Google (natural language)
- Answers must be 2-3 sentences, helpful, and conversational
- Mix question types: "Is it worth it?", "Is it waterproof?", "Battery life?", "Best price?", "How to set time?", "vs competitors?"
- Do NOT mention specific prices (they change)
- Answers should encourage reading the full review

Return ONLY a valid JSON array (no markdown, no extra text):
[
  {{"question": "...", "answer": "..."}},
  {{"question": "...", "answer": "..."}},
  {{"question": "...", "answer": "..."}},
  {{"question": "...", "answer": "..."}},
  {{"question": "...", "answer": "..."}},
  {{"question": "...", "answer": "..."}}
]"""

    max_attempts = len(GEMINI_API_KEYS) * 2
    for attempt in range(max_attempts):
        try:
            api_key = get_current_gemini_key()
            client = get_gemini_model(api_key)
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
            )
            raw = response.text.strip()
            raw = re.sub(r'```(?:json)?\s*', '', raw)
            raw = re.sub(r'```\s*', '', raw).strip()

            start = raw.find('[')
            end = raw.rfind(']') + 1
            if start == -1 or end == 0:
                raise ValueError("No JSON array found.")

            faqs = json.loads(raw[start:end])
            if not isinstance(faqs, list) or len(faqs) < 3:
                raise ValueError("Invalid FAQ list structure.")

            # Validate each item
            validated = []
            for item in faqs:
                if isinstance(item, dict) and item.get('question') and item.get('answer'):
                    validated.append({"question": item['question'], "answer": item['answer']})

            if len(validated) < 3:
                raise ValueError("Not enough valid FAQ items.")

            print(f"[AI] FAQ generated: {len(validated)} questions.")
            return validated

        except Exception as e:
            if is_quota_error(e):
                print(f"[AI:faq] Quota exceeded (attempt {attempt+1}). Switching key...")
                switch_to_next_gemini_key()
                time.sleep(2)
            else:
                print(f"[AI:faq] Error (attempt {attempt+1}): {e}. Switching key...")
                switch_to_next_gemini_key()
                time.sleep(1)

    print("[AI:faq] All retries exhausted. Using fallback FAQs.")
    return FALLBACK
