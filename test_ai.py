import ai_writer
from config import GEMINI_API_KEYS

print(f"Loaded keys: {len(GEMINI_API_KEYS)}")
content, social = ai_writer.generate_article(
    {"title": "Test Watch", "price": "$10", "rating": "5"}, 
    None, None, "English", None
)
print("Content generated successfully:")
print(content[:200] if content else "FAILED")
