import google.generativeai as genai
from config import GEMINI_API_KEY
import os
import sys

sys.path.append(os.getcwd())

genai.configure(api_key=GEMINI_API_KEY)
# Using the model found in the list
model = genai.GenerativeModel('gemini-2.0-flash')

try:
    print("Testing generation with gemini-2.0-flash...")
    response = model.generate_content("Hello, this is a test.")
    print("Success! Response: " + response.text)
except Exception as e:
    with open("error_log.txt", "w") as f:
        f.write(str(e))
    print(f"Error: {e}")
