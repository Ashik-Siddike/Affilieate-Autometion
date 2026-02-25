from config import GEMINI_API_KEYS, SCRAPINGANT_API_KEYS
import time
from youtubesearchpython import VideosSearch
import random
import requests
import re
import json
import google.generativeai as genai

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
    return genai.GenerativeModel('gemini-1.5-flash')

def find_review_video(product_name):
    """Searches YouTube for a review video and returns an embed code."""
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
        print(f"⚠️ Primary Video Search Failed: {e}")
        pass

    # --- FALLBACK: ScrapingAnt Search ---
    print("🔄 Attempting Fallback Video Search via ScrapingAnt...")
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
                     print("✅ Fallback Video Found!")
                     return embed_code
        except Exception as e:
            print(f"Fallback key failed: {e}")
            continue
            
    return ""

def generate_article(product_data, similar_products=None, internal_links=None, language='English', competitor_text=None):
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
        links_text = "### 🔗 Internal Links Context:\n"
        for p in internal_links:
            if isinstance(p, dict):
                links_text += f"- Link Title: '{p.get('title', 'Link')}' -> URL: {p.get('link', '#')}\n"

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

    # ======================================================
    # 📝 USER PROMPT (Structure & Content)
    # ======================================================
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
    - Use this exact Amazon link: {product_link}
    - Insert a "Check Price on Amazon" button after the Intro and at the very end.
    
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
    keys_tried = set()

    for attempt in range(max_attempts):
        current_key = get_current_gemini_key()
        
        try:
            # We construct the final prompt by combining system instruction and user prompt
            # This is safer for broader model compatibility if 'system_instruction' param is tricky
            final_prompt = system_instruction + "\n\n" + prompt
            
            genai.configure(api_key=current_key)
            
            # --- DYNAMIC MODEL DISCOVERY & EXECUTION ---
            response = None
            last_error = None
            
            # 1. Try Standard Preferred Models
            preferred_models = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-1.0-pro', 'gemini-pro']
            
            for model_name in preferred_models:
                try:
                    # print(f"Trying model: {model_name}...") 
                    model = genai.GenerativeModel(model_name)
                    response = model.generate_content(final_prompt)
                    if response:
                         print(f"✅ Generated using: {model_name}")
                         break
                except Exception as e:
                    # If it's a quota error, stop trying models on this key -> raise to outer loop to switch key
                    if is_quota_error(e):
                        raise e
                    # If it's a 404/Not Found, ignore and try next model
                    if "404" in str(e) or "not found" in str(e).lower():
                        continue
                    else:
                        # Unknown error (e.g. server error), maybe try next model or raise?
                        # Safer to raise if it's not a simple 'not found'
                        last_error = e
            
            # 2. If Standard Models Failed, Auto-Discover from Account
            if not response:
                print("⚠️ Standard models failed. Auto-discovering available models...")
                try:
                    all_models = list(genai.list_models())
                    # Filter for generation models
                    valid_models = [m.name for m in all_models if 'generateContent' in m.supported_generation_methods]
                    
                    if valid_models:
                        # Prefer Flash, then Pro
                        # Use first one found
                        best_model = next((m for m in valid_models if 'flash' in m), valid_models[0])
                        print(f"✅ Auto-selected available model: {best_model}")
                        
                        model = genai.GenerativeModel(best_model)
                        response = model.generate_content(final_prompt)
                    else:
                         print("❌ No valid generic models found on this key.")
                         # If we still have an error from loop, raise it to trigger key switch
                         if last_error: raise last_error
                         
                except Exception as discovery_e:
                    # If discovery fails (e.g. API disabled), raise to switch key
                    raise discovery_e
            
                if response and response.text:
                    # Success! (Handle Flash/Pro logic inside)
                    # We are in the loop, so we break out once successful.
                    # But first, parse JSON.
                    
                    content = response.text
                    social_data = {}

                    # Try to find JSON block at the end
                    json_match = re.search(r'```json\s*({.*?})\s*```', content, re.DOTALL)
                    if json_match:
                        try:
                            json_str = json_match.group(1)
                            social_data = json.loads(json_str)
                            # Remove the JSON from the main article content (HTML only)
                            content = content.replace(json_match.group(0), "").strip()
                        except:
                            pass # Parse error, ignore social
                    
                    # Clean up Markdown wrapper if present 
                    if content.startswith("```html"):
                        content = content.replace("```html", "").replace("```", "")
                    
                    # Fallback cleanup for ``` at start/end
                    content = content.strip('`').strip()
                        
                    return content, social_data
            
            # If we fall through here, it means auto-discovery also failed or returned None
            if not response:
                 print("❌ Auto-discovery failed or returned empty.")
                 if last_error: raise last_error

        except Exception as e:
            if is_quota_error(e):
                print(f"⚠️ Quota exceeded on current key. Switching...")
                switch_to_next_gemini_key()
                time.sleep(1)
            else:
                print(f"❌ Error generating article: {e}")
                # If it's not a quota error, maybe we shouldn't retry instantly, but let's try next key just in case
                switch_to_next_gemini_key()
                
    return None, None
