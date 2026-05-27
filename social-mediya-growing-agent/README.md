# Social Media Growing Agent

A standalone automation bot designed to warm up and organically grow social media profiles (Facebook, Instagram, X/Twitter, LinkedIn, Pinterest) before launching promotional or affiliate campaigns.

## Key Features

- **Educational Content Generator:** Prompts Gemini API using strict anti-AI tone guidelines (no fluff words, short conversational paragraphs) to generate highly engaging, platform-tailored copy.
- **API Key Rotation:** Rotates automatically through a pool of Gemini API keys to bypass rate limits or quota exhausts.
- **Dual Visual Styles (Pillow):** Dynamically compiles stunning 1080x1080 graphic cards to post on visual platforms.
  - *Glassmorphic Mode:* radial gradients with transparent white overlays and category highlights.
  - *Neo-Brutalist Mode:* solid dark backgrounds with offset neon shadow blocks, bold outlines, and asymmetric badges.
- **Cloudinary Integration:** Automatically uploads local image assets to Cloudinary to generate secure public URLs required by social APIs.
- **Webhook Dispatcher:** Triggers n8n and Make.com workflows with pre-formatted payloads.
- **Daemon Loop Mode:** Can run continuously as a background process with customizable interval posting.

---

## Setup & Installation

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/Ashik-Siddike/social-media-growing-agent.git
   cd social-media-growing-agent
   ```

2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment:**
   Copy `.env.example` to `.env` and fill in your credentials:
   ```bash
   cp .env.example .env
   ```

   Variables list:
   - `GEMINI_API_KEYS`: Comma-separated Gemini API keys for rotation.
   - `MAKE_WEBHOOK_URL` / `N8N_WEBHOOK_URL`: Your webhook triggers.
   - `CLOUDINARY_URL`: Cloudinary upload endpoint.
   - `BRAND_NAME`: Your page handle watermark (e.g. `Whitlogic`).
   - `POST_INTERVAL_HOURS`: Hours between background posts.

4. **Niche topics configuration:**
   Customize `topics.txt` with your own educational questions, facts, or tip topics (one per line).

---

## Usage

### Run a Single Post Cycle:
```bash
python main.py
```

### Run as a Continuous Background Daemon:
```bash
python main.py --loop
```
This will run the cycle and sleep for the configured `POST_INTERVAL_HOURS` before rotating to the next topic.
