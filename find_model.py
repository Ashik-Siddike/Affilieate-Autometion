import google.generativeai as genai
from config import GEMINI_API_KEY
import os
import sys

sys.path.append(os.getcwd())
genai.configure(api_key=GEMINI_API_KEY)

candidates = [
    'gemini-1.5-flash',
    'gemini-1.5-flash-001',
    'gemini-1.5-flash-latest',
    'gemini-flash-latest',
    'gemini-1.5-pro',
    'gemini-pro'
]

print("Testing model candidates...")
for model_name in candidates:
    print(f"Testing {model_name}...")
    model = genai.GenerativeModel(model_name)
    try:
        model.generate_content("Hello")
        print(f"SUCCESS: {model_name} works!")
        break
    except Exception as e:
        print(f"FAILED {model_name}: {e}")
