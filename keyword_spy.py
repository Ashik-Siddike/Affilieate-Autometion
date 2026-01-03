import requests
import re
import json
import google.generativeai as genai
from config import SCRAPINGANT_API_KEYS, GEMINI_API_KEYS
from ai_writer import get_current_gemini_key

def scrape_and_extract_keywords(url):
    """
    1. Scrapes headings (H1, H2, H3) from a URL.
    2. Uses Gemini to analyze them and extract target keywords.
    """
    # 1. Scrape Content
    html = ""
    success = False
    
    print(f"🕵️ Spying on: {url}...")
    
    for api_key in SCRAPINGANT_API_KEYS:
        try:
            response = requests.get(
                "https://api.scrapingant.com/v2/general",
                params={'url': url, 'browser': 'true'},
                headers={'x-api-key': api_key},
                timeout=60
            )
            if response.status_code == 200:
                html = response.text
                success = True
                break
        except Exception as e:
            print(f"Scrape error: {e}")
            continue
            
    if not success:
        return {"error": "Failed to scrape URL. Check validity or try again."}

    # 2. Extract Headings (Simple Regex)
    headings = []
    for tag in ['h1', 'h2', 'h3']:
        matches = re.findall(r'<' + tag + r'[^>]*>(.*?)</' + tag + r'>', html, re.DOTALL | re.IGNORECASE)
        # Clean HTML tags from inside headings
        clean_matches = [re.sub(r'<[^>]+>', '', m).strip() for m in matches if len(m) > 5]
        headings.extend(clean_matches[:10]) # Top 10 of each
        
    if not headings:
        return {"error": "No headings found. The page might be empty or protected."}
        
    heading_text = "\n".join(headings[:50]) # Max 50 headings total
    
    # 3. AI Analysis
    try:
        current_key = get_current_gemini_key()
        genai.configure(api_key=current_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        Analyze these article headings from a competitor's website:
        
        {heading_text}
        
        TASK:
        Identify the likely **Target SEO Keywords** (Buying intent) they are optimizing for.
        Return a valid JSON list of 5-10 strings.
        Example: ["best gaming laptop", "cheap laptop for students"]
        
        JSON ONLY:
        """
        
        response = model.generate_content(prompt)
        text = response.text.replace('```json', '').replace('```', '').strip()
        keywords = json.loads(text)
        
        return {"keywords": keywords, "headings_count": len(headings)}
        
    except Exception as e:
        return {"error": f"AI Analysis Failed: {e}"}
