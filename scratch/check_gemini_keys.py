import os
import re
import requests
import sys

# Force output encoding to utf-8 to avoid CP1252 errors on Windows
sys.stdout.reconfigure(encoding='utf-8')

def test_keys():
    env_path = "../.env"
    if not os.path.exists(env_path):
        env_path = ".env"
    
    with open(env_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    match = re.search(r"GEMINI_API_KEYS=(.+)", content)
    if not match:
        print("No GEMINI_API_KEYS found in .env")
        return
    
    keys_str = match.group(1).strip()
    if keys_str.startswith('"') and keys_str.endswith('"'):
        keys_str = keys_str[1:-1]
    elif keys_str.startswith("'") and keys_str.endswith("'"):
        keys_str = keys_str[1:-1]
        
    keys = [k.strip() for k in keys_str.split(",") if k.strip()]
    print(f"Loaded {len(keys)} keys from .env. Testing each key...")
    
    working_keys = []
    suspended_keys = []
    
    for i, key in enumerate(keys):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": "Hello"}]}]
        }
        
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=10)
            if resp.status_code == 200:
                print(f"Key {i+1} ({key[:10]}...): WORKING")
                working_keys.append(key)
            elif resp.status_code == 403:
                print(f"Key {i+1} ({key[:10]}...): SUSPENDED/FORBIDDEN (HTTP 403: {resp.text[:100]})")
                suspended_keys.append(key)
            elif resp.status_code == 429:
                print(f"Key {i+1} ({key[:10]}...): RATE LIMITED/EXHAUSTED (HTTP 429)")
                working_keys.append(key)
            else:
                print(f"Key {i+1} ({key[:10]}...): ERROR {resp.status_code} ({resp.text[:100]})")
                suspended_keys.append(key)
        except Exception as e:
            print(f"Key {i+1} ({key[:10]}...): CONNECTION ERROR ({str(e)})")
            suspended_keys.append(key)

    print("\n--- RESULTS ---")
    print(f"Total: {len(keys)}")
    print(f"Working/Rate-limited: {len(working_keys)} (kept)")
    print(f"Suspended/Broken: {len(suspended_keys)} (deleted)")
    
    if suspended_keys:
        new_keys_str = ",".join(working_keys)
        new_content = re.sub(r"GEMINI_API_KEYS=.+", f"GEMINI_API_KEYS={new_keys_str}", content)
        with open(env_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print("Updated .env file to remove suspended keys! Programmatic cleanup complete.")
    else:
        print("No keys removed.")

if __name__ == "__main__":
    test_keys()
