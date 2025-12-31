from config import GEMINI_API_KEYS, SCRAPINGANT_API_KEYS
import os

print("--- DEBUGGING API KEY LOADING ---")
print(f"Loaded {len(GEMINI_API_KEYS)} Gemini Keys.")
print(f"Loaded {len(SCRAPINGANT_API_KEYS)} ScrapingAnt Keys.")

if GEMINI_API_KEYS:
    print("Gemini Suffixes:")
    for k in GEMINI_API_KEYS:
        print(f"   ...{k[-5:] if len(k) > 5 else k}")
else:
    print("NO Gemini keys loaded!")

print("-" * 30)

if SCRAPINGANT_API_KEYS:
    print("ScrapingAnt Suffixes:")
    for k in SCRAPINGANT_API_KEYS:
        print(f"   ...{k[-5:] if len(k) > 5 else k}")
else:
    print("NO ScrapingAnt keys loaded!")
