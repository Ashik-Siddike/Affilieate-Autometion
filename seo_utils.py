import re
import math

class SEOChecker:
    def __init__(self):
        pass

    def analyze(self, content, keyword):
        """
        Analyzes the HTML content and returns an SEO score (0-100) and feedback.
        """
        score = 0
        feedback = []
        
        # Strip HTML for word count analysis
        clean_text = re.sub('<[^<]+?>', '', content)
        words = clean_text.split()
        word_count = len(words)
        
        # 1. Word Count Check (20 points)
        if word_count > 1000:
            score += 20
        elif word_count > 600:
            score += 15
        elif word_count > 300:
            score += 10
        else:
            feedback.append("⚠️ Content is too short (<300 words).")

        # 2. Keyword Density (30 points)
        if keyword:
            keyword_lower = keyword.lower()
            text_lower = clean_text.lower()
            kw_count = text_lower.count(keyword_lower)
            
            if word_count > 0:
                density = (kw_count / word_count) * 100
            else:
                density = 0
                
            if 0.5 <= density <= 2.5:
                score += 30
            elif density > 2.5:
                score += 15
                feedback.append(f"⚠️ Keyword density is high ({density:.2f}%). Risk of stuffing.")
            elif density < 0.5:
                score += 10
                feedback.append(f"⚠️ Keyword density is low ({density:.2f}%). Use '{keyword}' more.")
        else:
            score += 30 # No keyword provided, skip penalty
            
        # 3. Headings Presence (20 points)
        # We assume content is an HTML body, so we look for <h2> or <h3>
        h2_count = len(re.findall(r'<h2', content, re.IGNORECASE))
        h3_count = len(re.findall(r'<h3', content, re.IGNORECASE))
        
        if h2_count >= 2:
            score += 20
        elif h2_count == 1:
            score += 10
            feedback.append("💡 Use more Subheadings (H2) to structure content.")
        else:
            feedback.append("⚠️ No H2 headings found.")

        # 4. Images Presence (15 points)
        img_count = len(re.findall(r'<img', content, re.IGNORECASE))
        if img_count >= 1:
            score += 15
        else:
            feedback.append("💡 Add at least one image.")

        # 5. Readability / Paragraph Length (15 points)
        # Simple check: Average words per paragraph
        # We split by <p> tags
        paragraphs = re.findall(r'<p>(.*?)</p>', content, re.DOTALL)
        if paragraphs:
            long_paragraphs = 0
            for p in paragraphs:
                p_text = re.sub('<[^<]+?>', '', p)
                if len(p_text.split()) > 150: # Arbitrary "too long" threshold
                    long_paragraphs += 1
            
            if long_paragraphs == 0:
                score += 15
            else:
                score += 5
                feedback.append(f"⚠️ Found {long_paragraphs} long paragraphs. Break them up.")
        else:
            # Maybe raw text or div based
            score += 10 

        return {
            "score": min(100, score),
            "word_count": word_count,
            "keyword_density": f"{density:.2f}%" if keyword and word_count > 0 else "N/A",
            "feedback": feedback
        }

# Example Usage
if __name__ == "__main__":
    checker = SEOChecker()
    dummy_html = "<h1>Test</h1><p>This is a test content with the keyword test.</p>"
    print(checker.analyze(dummy_html, "test"))
