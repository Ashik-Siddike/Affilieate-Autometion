from bs4 import BeautifulSoup

with open('scratch/scraped.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

print("Page Title:", soup.title.string if soup.title else "No Title")

# Find all links
links = soup.find_all('a')
print(f"Total links: {len(links)}")
for link in links[:20]:
    print("Link:", link.get('href'), link.text.strip()[:50])

# Find all divs containing text longer than 20 chars (might be titles)
import re
divs = soup.find_all('div')
long_texts = set()
for div in divs:
    text = div.get_text(strip=True)
    if 20 < len(text) < 150 and re.search(r'[a-zA-Z]{5,}', text):
        long_texts.add(text)

print(f"\nFound {len(long_texts)} possible text snippets.")
for t in list(long_texts)[:10]:
    print("-", t)
