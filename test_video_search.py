from ai_writer import find_review_video
from youtubesearchpython import VideosSearch

def test_video_search():
    keyword = "iPhone 15 Pro Max"
    print(f"🔎 Searching for video: {keyword}")
    
    # Direct debug
    try:
        query = f"{keyword} review"
        print("Calling VideosSearch...")
        videosSearch = VideosSearch(query, limit = 1)
        results = videosSearch.result()
        print(f"RAW RESULT KEYS: {results.keys()}")
        if 'result' in results:
             print(f"Number of videos found: {len(results['result'])}")
             if results['result']:
                 print(f"First Video ID: {results['result'][0]['id']}")
        else:
            print("No 'result' key in response.")
            print(results)
    except Exception as e:
        print(f"DIRECT DEBUG ERROR: {e}")

    embed = find_review_video(keyword)
    
    if embed:
        print("✅ SUCCESS! Video Embed Code found")
        # print(embed) 
    else:
        print("❌ FAILED. find_review_video returned empty.")

if __name__ == "__main__":
    test_video_search()
