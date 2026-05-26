import os
import requests
from dotenv import load_dotenv

load_dotenv("e:/projects/WeeklyProject/Affilieate-Autometion/.env")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

url = f"{SUPABASE_URL}/rest/v1/sites?limit=1"
try:
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        if data:
            print("Columns in sites table:")
            for key in data[0].keys():
                print(f"- {key}")
        else:
            print("No rows found. Can't infer schema easily from empty table.")
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Exception: {e}")
