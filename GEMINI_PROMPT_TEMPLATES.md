# 🚀 Gemini API - Reusable Prompt Template Library

## বাংলা নোট (Bengali Note):
এই ফাইলটি আপনার নতুন প্রজেক্টে সরাসরি ব্যবহার করার জন্য তৈরি। শুধু variables পরিবর্তন করে same structure অনুসরণ করুন।

---

## 📦 TEMPLATE 1: PRODUCT REVIEW GENERATOR (From Affiliate Project)

### Use Case:
Generate detailed, human-like product reviews with HTML formatting and social media metadata.

### Implementation:

```python
import google.generativeai as genai
import json
import re
import time

class ProductReviewGenerator:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    def generate_review(self, product_data, context_data=None):
        """
        Args:
            product_data: {
                'title': str,
                'price': str,
                'rating': str,
                'review_count': str,
                'product_url': str,
                'description': str (optional)
            }
            context_data: {
                'similar_products': list,
                'internal_links': list,
                'competitor_text': str,
                'video_embed': str,
                'language': str
            }
        """
        
        # === SYSTEM INSTRUCTION ===
        system_instruction = """
You are an Expert Product Tester & Consumer Advocate.
Your goal is to write reviews that feel 100% human, honest, and personal.

🌍 **LANGUAGE REQUIREMENT:**
You MUST write the ENTIRE ARTICLE in **{language}**.

❌ **FORBIDDEN AI WORDS (Never use these):**
Unleash, Unlock, Realm, Landscape, Tapestry, Symphony, Game-changer, 
Delve, Dive deep, Bustling, Vibrant, Meticulous, Paramount, Elevate.

✅ **TONE & STYLE (Must follow):**
- Conversational: Write like talking to a friend. Use "I", "We", "You".
- Direct: Don't fluff. Get to the point.
- Varied Syntax: Mix short punchy + longer descriptive sentences.
- Experience: Simulate real testing. Say "I felt..." or "In my testing...".
        """.format(language=context_data.get('language', 'English') if context_data else 'English')
        
        # === BUILD CONTEXT SECTIONS ===
        comparison_text = ""
        if context_data and context_data.get('similar_products'):
            comparison_text = "### 📊 Comparison Data:\n"
            for p in context_data['similar_products']:
                comparison_text += f"- Compare: {p['title']} | Price: {p['price']} | Rating: {p['rating']}\n"
        
        links_text = ""
        if context_data and context_data.get('internal_links'):
            links_text = "### 🔗 Internal Links Context:\n"
            for p in context_data['internal_links']:
                links_text += f"- Link: '{p['title']}' -> {p['link']}\n"
        
        video_instruction = ""
        if context_data and context_data.get('video_embed'):
            video_instruction = f"""
**🎥 VIDEO EMBEDDING INSTRUCTION:**
Insert this HTML right before the 'Final Conclusion' section:

{context_data['video_embed']}

Do not alter the HTML code.
            """
        
        skyscraper_instruction = ""
        if context_data and context_data.get('competitor_text'):
            skyscraper_instruction = f"""
### 🕵️ COMPETITOR INTELLIGENCE (SKYSCRAPER MODE)
Reference content from top-ranking competitor:
{context_data['competitor_text'][:2000]}...

**YOUR MISSION:**
1. Write DEEPER, More Helpful, Better Structured content.
2. Identify points they missed and include them.
3. Do NOT copy their text. Use as quality benchmark.
            """
        
        # === USER PROMPT ===
        user_prompt = f"""
Write a complete, HTML-formatted product review for: **{product_data['title']}**

**Product Info:**
- Price: {product_data['price']} | Rating: {product_data['rating']} stars ({product_data['review_count']} reviews)

{comparison_text}
{links_text}
{video_instruction}
{skyscraper_instruction}

### 🧱 STRICT OUTPUT STRUCTURE (HTML BODY ONLY) 🧱

**1. ⚡ Quick Verdict (Featured Snippet Bait)**
- Start with `<h2>Quick Verdict</h2>`
- Direct Yes/No recommendation in bold
- 40-50 word summary answering "Is it worth buying?"

**2. 🔑 Key Takeaways**
- `<h2>Key Takeaways</h2>`
- Bulleted list (3-4 most important items)

**3. 📦 Introduction**
- Personal hook: Why does this product exist? Who needs it?

**4. 🛠️ Build & Design**
- Use `<h2>` and `<h3>` headings
- Discuss quality, materials, and feel

**5. 🏆 Performance / In-Depth Testing**
- Detailed analysis with specific features mentioned
- Real testing experience

**6. 🆚 Comparison (If data provided)**
- Create responsive HTML table
- Compare with similar products

**7. ✅ Pros & ❌ Cons**
- Use styled HTML table
- Green background for Pros, Red for Cons

**8. ❓ FAQ (Voice Search Optimization)**
- `<h2>FAQ</h2>`
- Include 3 common questions about this product type
- Concise answers (good for Google "People Also Ask")

**9. 🎯 Final Conclusion**
- Who exactly should buy this?
- Persona-based recommendation

**CTA Requirements:**
- Use this exact Amazon link: {product_data['product_url']}
- Insert "Check Price on Amazon" button after Intro and at very end

**Formatting:**
- Output raw HTML body only (no markdown wrapper)
- Use <h2>, <h3>, <p>, <ul>, <li>, <strong>, <em>

**10. 📢 Social Media Bundle (JSON)**
At the VERY END, generate strictly valid JSON:

```json
{{
  "tweet": "Viral, click-baity tweet (max 280 chars) with hashtags.",
  "pinterest_title": "Catchy Pinterest pin title.",
  "pinterest_desc": "100-word SEO-optimized description for Pinterest.",
  "linkedin": "Professional but engaging LinkedIn post summary."
}}
```

Ensure JSON is valid and separated from HTML.
        """
        
        # === MAKE API CALL ===
        try:
            final_prompt = system_instruction + "\n\n" + user_prompt
            response = self.model.generate_content(final_prompt)
            
            if response and response.text:
                content = response.text
                
                # Extract JSON from response
                json_match = re.search(r'```json\s*({.*?})\s*```', content, re.DOTALL)
                social_data = {}
                
                if json_match:
                    try:
                        json_str = json_match.group(1)
                        social_data = json.loads(json_str)
                        content = content.replace(json_match.group(0), "").strip()
                    except json.JSONDecodeError:
                        pass
                
                # Clean markdown wrappers
                if content.startswith("```html"):
                    content = content.replace("```html", "").replace("```", "")
                
                content = content.strip('`').strip()
                
                return {
                    'html_content': content,
                    'social_media': social_data,
                    'success': True
                }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

# === USAGE EXAMPLE ===
if __name__ == "__main__":
    generator = ProductReviewGenerator(api_key="YOUR_GEMINI_API_KEY")
    
    product = {
        'title': 'PlayStation 5 Controller',
        'price': '$69.99',
        'rating': '4.8',
        'review_count': '5,234',
        'product_url': 'https://amazon.com/...',
    }
    
    context = {
        'language': 'English',
        'similar_products': [
            {'title': 'Xbox Controller', 'price': '$59.99', 'rating': '4.5'},
            {'title': 'Nintendo Pro Controller', 'price': '$69.99', 'rating': '4.6'},
        ],
        'internal_links': [
            {'title': 'Best Gaming Headsets 2025', 'link': 'https://yoursite.com/headsets'},
        ],
    }
    
    result = generator.generate_review(product, context)
    
    if result['success']:
        print("✅ Review Generated!")
        print(result['html_content'][:500])
        print(result['social_media'])
    else:
        print(f"❌ Error: {result['error']}")
```

---

## 📝 TEMPLATE 2: BLOG ARTICLE WRITER (Adapted Version)

### Use Case:
Generate long-form SEO articles with internal linking and schema markup.

```python
class BlogArticleWriter:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-pro')
    
    def generate_article(self, topic, keywords, content_type='guide'):
        """
        Args:
            topic: str - Main topic
            keywords: list - Target SEO keywords
            content_type: str - 'guide', 'how-to', 'comparison', 'review'
        """
        
        system_instruction = """
You are an Expert SEO Content Writer and Journalist.
Write articles that rank on Google, educate readers, and feel authentic.

📊 **SEO GUIDELINES:**
- Use H2 and H3 headings strategically
- Include natural keyword variations (LSI keywords)
- Write for E-E-A-T: Experience, Expertise, Authority, Trustworthiness
- Target featured snippets with direct answers

✅ **STRUCTURE:**
- Engaging introduction (200 words)
- Clear outline with H2s
- Detailed sections with H3s and examples
- Real data and statistics
- Natural internal links
- Strong conclusion with CTA
        """
        
        keywords_str = ", ".join(keywords)
        
        user_prompt = f"""
Write a comprehensive {content_type.upper()} article about: **{topic}**

**Target Keywords:**
{keywords_str}

**Requirements:**
1. Length: 2000-2500 words
2. Include at least 3 subheadings (H3) per main section
3. Use numbered lists for step-by-step content
4. Include at least 2 comparison tables (if comparison article)
5. Add real statistics and data points
6. Natural language - no AI buzzwords
7. Include 3-4 call-to-action suggestions
8. Suggest 5 internal link anchor texts at the end

**Output:**
Raw HTML body content only.

**Tone:**
Conversational, expert, helpful, slightly informal.
        """
        
        try:
            final_prompt = system_instruction + "\n\n" + user_prompt
            response = self.model.generate_content(final_prompt)
            
            if response and response.text:
                content = response.text.strip('`').strip()
                return {
                    'content': content,
                    'word_count': len(content.split()),
                    'success': True
                }
        except Exception as e:
            return {'success': False, 'error': str(e)}

# === USAGE ===
writer = BlogArticleWriter(api_key="YOUR_API_KEY")
result = writer.generate_article(
    topic="Best Gaming Laptops 2025",
    keywords=["gaming laptop", "budget gaming laptop", "RTX 4060"],
    content_type="comparison"
)
```

---

## 🎨 TEMPLATE 3: EMAIL COPYWRITER

### Use Case:
Generate high-converting email sequences for marketing campaigns.

```python
class EmailCopywriter:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    def generate_email_sequence(self, product_info, audience, campaign_type):
        """
        Args:
            product_info: dict with product details
            audience: str - Target audience description
            campaign_type: str - 'welcome', 'launch', 'urgency', 'retention'
        """
        
        system_instruction = """
You are an Expert Email Copywriter specializing in high-conversion campaigns.

📧 **EMAIL WRITING FORMULA:**
- Subject: 50 chars max, curiosity-driven, personalized
- Preview: 50 chars max, teaser
- Body: Conversational, benefit-focused, scannable
- CTA: Action-oriented, urgent but not spammy
- Signature: Professional with social links

❌ **AVOID:**
- Overuse of exclamation marks (max 1 per email)
- All caps (except 2-3 words)
- Generic subject lines
- Long paragraphs (max 3 lines)
- Multiple CTAs (focus on 1 primary action)
        """
        
        user_prompt = f"""
Write a {campaign_type.upper()} email campaign for:

**Product:** {product_info.get('name')}
**Audience:** {audience}
**Campaign Type:** {campaign_type}

**Generate 3 Email Variations:**

For each email, provide:
1. Subject Line
2. Preview Text
3. Email Body (HTML)
4. Primary CTA Button Text
5. Expected Click-Through Rate

**Requirements:**
- Personalize with [FIRST_NAME] placeholder
- Include benefit-driven copy
- Add social proof if applicable
- Make it mobile-friendly
- Keep body under 200 words
- Include one discount/offer if launch campaign
        """
        
        try:
            response = self.model.generate_content(
                system_instruction + "\n\n" + user_prompt
            )
            
            if response:
                return {
                    'emails': response.text,
                    'success': True
                }
        except Exception as e:
            return {'success': False, 'error': str(e)}
```

---

## 🎯 TEMPLATE 4: SOCIAL MEDIA CONTENT CREATOR

### Use Case:
Generate engaging social media content with optimal hashtags and formatting.

```python
class SocialMediaContentCreator:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    def generate_social_content(self, topic, platforms, tone='casual'):
        """
        Args:
            topic: str - Content topic
            platforms: list - ['twitter', 'instagram', 'linkedin', 'tiktok']
            tone: str - 'casual', 'professional', 'funny', 'inspirational'
        """
        
        system_instruction = f"""
You are a Social Media Content Strategist with expertise in {', '.join(platforms)}.

✅ **PLATFORM GUIDELINES:**
- Twitter: 280 chars max, witty, timely
- Instagram: Engaging hook, call-to-action, 10-15 hashtags
- LinkedIn: Professional, thought leadership, authentic
- TikTok: Trendy, concise, hook in first 3 seconds

🎯 **TONE:** {tone.upper()}

❌ **FORBIDDEN:**
- Too many emojis (max 2-3)
- Hashtag spam
- Self-promotional (be helpful first)
- AI-generated buzzwords
        """
        
        platforms_str = ", ".join(platforms)
        
        user_prompt = f"""
Create engaging social media content about: **{topic}**

**Platforms:** {platforms_str}
**Tone:** {tone}

**For each platform, provide:**
1. Main Post Text
2. Recommended Hashtags
3. Best Time to Post
4. CTA
5. Expected Engagement Rate

**Bonus:** 
Generate 3 carousel post ideas (Instagram/LinkedIn) with descriptions.
        """
        
        try:
            response = self.model.generate_content(
                system_instruction + "\n\n" + user_prompt
            )
            
            if response and response.text:
                return {
                    'content': response.text,
                    'success': True
                }
        except Exception as e:
            return {'success': False, 'error': str(e)}
```

---

## 📊 TEMPLATE 5: DATA ANALYSIS & REPORT WRITER

### Use Case:
Generate analysis reports from structured data.

```python
class DataAnalysisReporter:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-pro')
    
    def generate_analysis_report(self, data_summary, industry, metrics):
        """
        Args:
            data_summary: str - Summary of data analyzed
            industry: str - Industry vertical
            metrics: dict - Key metrics and findings
        """
        
        system_instruction = """
You are an Expert Business Intelligence Analyst.
Generate insightful, data-driven reports that tell a story.

📊 **REPORT STRUCTURE:**
- Executive Summary (Key Findings)
- Detailed Analysis by Category
- Trends and Patterns
- Competitive Benchmarking
- Recommendations & Next Steps

✅ **STYLE:**
- Data-driven conclusions
- Use percentages and comparisons
- Actionable insights
- Professional but accessible
        """
        
        user_prompt = f"""
Generate a comprehensive analysis report:

**Industry:** {industry}
**Data Summary:** {data_summary}

**Key Metrics to Include:**
{json.dumps(metrics, indent=2)}

**Report Should Include:**
1. Executive Summary (150 words)
2. Detailed Findings (3-4 sections)
3. Data Visualizations Suggestions
4. Competitive Comparison
5. 5 Actionable Recommendations
6. Risk Analysis
7. Forecast for next 6 months
        """
        
        try:
            response = self.model.generate_content(
                system_instruction + "\n\n" + user_prompt
            )
            
            if response and response.text:
                return {
                    'report': response.text,
                    'success': True
                }
        except Exception as e:
            return {'success': False, 'error': str(e)}
```

---

## ⚙️ UNIVERSAL API KEY ROTATION & ERROR HANDLING

Use this wrapper for ANY template above:

```python
import time

class GeminiAPIManager:
    def __init__(self, api_keys_list):
        """
        Args:
            api_keys_list: list of Gemini API keys
        """
        self.api_keys = api_keys_list
        self.current_index = 0
    
    def get_current_key(self):
        return self.api_keys[self.current_index]
    
    def switch_to_next_key(self):
        self.current_index = (self.current_index + 1) % len(self.api_keys)
        print(f"🔄 Switched to API key {self.current_index + 1}/{len(self.api_keys)}")
    
    def is_quota_error(self, error):
        error_str = str(error).lower()
        quota_indicators = ["429", "quota exceeded", "resource exhausted", "rate limit", "403", "billing"]
        return any(indicator in error_str for indicator in quota_indicators)
    
    def call_with_retry(self, callback, max_attempts=None):
        """
        Universal retry wrapper.
        
        Args:
            callback: function(api_key) -> response
            max_attempts: default = len(keys) * 2
        """
        if max_attempts is None:
            max_attempts = len(self.api_keys) * 2
        
        for attempt in range(max_attempts):
            try:
                current_key = self.get_current_key()
                result = callback(current_key)
                return result
            
            except Exception as e:
                if self.is_quota_error(e):
                    print(f"⚠️ Quota exceeded. Switching key...")
                    self.switch_to_next_key()
                    time.sleep(1)
                else:
                    print(f"❌ Error: {e}")
                    self.switch_to_next_key()
        
        return None

# === USAGE WITH ANY TEMPLATE ===
api_manager = GeminiAPIManager([
    "AIzaSy_KEY_1_HERE",
    "AIzaSy_KEY_2_HERE",
    "AIzaSy_KEY_3_HERE",
])

def my_generation_callback(api_key):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    return model.generate_content("Your prompt here")

result = api_manager.call_with_retry(my_generation_callback)
```

---

## 🎬 QUICK START CHECKLIST

### For ANY new project:

- [ ] **Install:** `pip install google-generativeai python-dotenv`
- [ ] **Setup .env:** Add `GEMINI_API_KEYS=AIzaSy_...,AIzaSy_...,AIzaSy_...`
- [ ] **Choose Template:** Pick 1-5 based on your use case
- [ ] **Copy Class:** Copy entire class to your project
- [ ] **Update Variables:** Change `api_key`, inputs, outputs
- [ ] **Add Error Handling:** Use `GeminiAPIManager` wrapper
- [ ] **Test:** Run with one API key first, then add rotation
- [ ] **Deploy:** Monitor logs and adjust prompts as needed

---

## 📚 TEMPLATE REFERENCE TABLE

| Template | Use Case | Best Model | Est. Cost |
|----------|----------|-----------|-----------|
| 1. Product Review | E-commerce, affiliates | gemini-1.5-flash | Low |
| 2. Blog Article | Content marketing, SEO | gemini-1.5-pro | Medium |
| 3. Email Copywriting | Marketing automation | gemini-1.5-flash | Low |
| 4. Social Media | Social strategy | gemini-1.5-flash | Low |
| 5. Data Analysis | Business intelligence | gemini-1.5-pro | Medium |

---

## 💡 PRO TIPS

1. **Test with flash first** → Cheaper and faster for simple tasks
2. **Use pro for complex** → Better for multi-step reasoning
3. **Add delays** → Use `time.sleep(1)` between requests to avoid rate limits
4. **Clean outputs** → Always strip markdown wrappers (`\`\`\``)
5. **Extract JSON** → Use regex to find and parse JSON blocks
6. **Monitor logs** → Log every API call for debugging
7. **Fallback models** → List multiple models in case some aren't available
8. **Batch requests** → Generate multiple items per API call when possible

---

**Created:** January 18, 2026  
**Source Project:** Amazon Affiliate Automation Bot  
**Compatible With:** Any Python 3.8+ project  
**License:** Free to reuse and modify
