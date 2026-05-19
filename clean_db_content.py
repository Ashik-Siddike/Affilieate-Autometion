import sys, re
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, '.')

from config import SUPABASE_URL, SUPABASE_KEY
import requests

SOCIAL_KEYS = ['"fb_content"', '"pin_title"', '"ig_content"', '"x_content"']

def clean_social_from_content(content):
    if not content:
        return content, False
    original = content

    # Strategy 1: remove ```json...``` block
    content = re.sub(r'```json.*?```', '', content, flags=re.DOTALL)

    # Strategy 2: remove from first { that contains social keys
    for key in SOCIAL_KEYS:
        idx = content.find(key)
        if idx != -1:
            brace_pos = content.rfind('{', 0, idx)
            if brace_pos != -1:
                content = content[:brace_pos].strip()
            break

    # Clean stray code fences
    content = re.sub(r'```(?:html|json)?\s*', '', content)
    content = content.strip('`').strip()

    changed = (content != original)
    return content, changed

# Fetch all posts
headers = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'Content-Type': 'application/json',
    'Prefer': 'return=representation'
}

resp = requests.get(
    f'{SUPABASE_URL}/rest/v1/Post?select=id,content&limit=200',
    headers=headers
)
posts = resp.json()
if not isinstance(posts, list):
    print(f'Unexpected response: {posts}')
    sys.exit(1)
print(f'Found {len(posts)} posts.')

fixed = 0
for post in posts:
    pid     = post.get('id')
    content = post.get('content', '')
    cleaned, changed = clean_social_from_content(content)
    if changed:
        patch_url = f'{SUPABASE_URL}/rest/v1/Post?id=eq.{pid}'
        r = requests.patch(patch_url, headers=headers, json={'content': cleaned})
        status = 'FIXED' if r.status_code in [200, 204] else f'ERROR({r.status_code}: {r.text[:80]})'
        print(f'[{status}] id={pid}')
        if r.status_code in [200, 204]:
            fixed += 1

print(f'\nDone. Fixed {fixed}/{len(posts)} posts.')
