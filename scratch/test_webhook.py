"""
test_webhook.py - Send a test payload to Make.com to register new fields.
Run: python test_webhook.py
"""
import requests
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import MAKE_WEBHOOK_URL

payload = {
    "title": "SKMEI 1251 Men Sports Watch Waterproof LED Digital",
    "url": "https://whitlogic.online/watch-reviews/skmei-1251-test",
    "imageUrl": "https://dummyimage.com/800x800/1c2030/fbbf24.png&text=SKMEI+Watch",
    "pinterestImageUrl": "https://dummyimage.com/1000x1500/1c2030/fbbf24.png&text=SKMEI+Watch+Pinterest",
    "amazonUrl": "https://www.amazon.com/dp/B01SAMPLE?tag=ashiksiddike-20",
    "keyword": "best budget tactical watch 2025",
    "brand": "SKMEI",
    # ✅ NEW FIELDS - Platform-specific AI content
    "fb_content": "🔥 Jaw-dropping value! The SKMEI 1251 is the budget tactical watch you've been waiting for.\n\n⌚ Military-grade build, 50M waterproof, and under $20? We tested it so you don't have to!\n\n✅ Read the full review → https://whitlogic.online/watch-reviews/skmei-1251-test\n\n#TacticalWatch #BudgetWatch #SKMEI #GearReview #Amazon",
    "ig_content": "⌚ The SKMEI 1251 is INSANE value for money! 🔥\n\n💪 Military-grade build quality\n🌊 50M waterproof rating\n⚡ LED backlight display\n💰 Under $20 on Amazon!\n\nWould you wear this? Drop a 👇 in the comments!\n\nLink in bio!\n\n#SKMEI #TacticalWatch #BudgetWatch #WatchOfTheDay #WatchFam #MensWatch #SportWatch #OutdoorGear #AmazonFinds #AffiliateMarketing #ProductReview #GearHead #WatchCollector #MilitaryWatch #EDC",
    "pin_title": "SKMEI 1251 Review: Best Budget Tactical Watch Under $20",
    "pin_desc": "Looking for a tough, affordable tactical watch? The SKMEI 1251 delivers military-grade durability, 50M waterproofing, and LED display — all under $20! Read our full expert review at https://whitlogic.online/watch-reviews/skmei-1251-test\n\n#TacticalWatch #BudgetWatch #SKMEI #WatchReview #Amazon",
    "linkedin_content": "🔎 I just published a detailed breakdown of the SKMEI 1251 — one of the best value-for-money tactical watches available today.\n\nFor under $20, you get military-grade build quality, 50M waterproofing, and a clean LED display. It's a remarkable example of how affordable doesn't mean cheap.\n\nFull review here → https://whitlogic.online/watch-reviews/skmei-1251-test\n\n#ProductReview #ValueForMoney #AffiliateMarketing #WatchReview",
}

print("=" * 60)
print("Sending test payload to Make.com webhook...")
print(f"URL: {MAKE_WEBHOOK_URL}")
print(f"Fields: {list(payload.keys())}")
print("=" * 60)

try:
    r = requests.post(MAKE_WEBHOOK_URL, json=payload, timeout=15)
    print(f"\n✅ Status: {r.status_code}")
    print(f"Response: {r.text[:200]}")
    if r.status_code in (200, 201, 202, 204):
        print("\n🎉 SUCCESS! Make.com has received the payload.")
        print("Go back to Make.com and it should now show all the new fields:")
        print("  - fb_content ✅")
        print("  - ig_content ✅")
        print("  - pin_title ✅")
        print("  - pin_desc ✅")
        print("  - linkedin_content ✅")
        print("  - pinterestImageUrl ✅")
    else:
        print(f"\n⚠️  Unexpected status code: {r.status_code}")
except Exception as e:
    print(f"\n❌ Error: {e}")
