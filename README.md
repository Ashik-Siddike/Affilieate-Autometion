# 🤖 Amazon Affiliate Automation Bot

A powerful, fully automated Python bot designed to build and scale Amazon Affiliate niche sites on autopilot. It discovers products, generates SEO-optimized content with AI, publishes to WordPress, and syndicates to social media via n8n.

## ✨ Key Features

*   **🔍 Auto-Discovery**: Automatically searches Amazon for profitable products based on your niche keywords.
*   **🧠 AI-Powered Content**: Uses Google Gemini Pro to write engaging, SEO-friendly product reviews.
*   **📊 Comparison Tables**: Automatically generates HTML comparison tables with similar products found in the database.
*   **🔗 Smart Internal Linking**: Contextually inserts links to your previously published articles to boost SEO.
*   **📝 JSON-LD Schema**: Auto-generates `Product` schema markup for rich snippets in Google search results.
*   **WordPress Integration**: Publishes formatted articles directly to your WordPress site with featured images.
*   **🌐 Social Media Syndication**: Triggers an advanced **n8n** workflow to auto-post to Pinterest, Facebook, X, LinkedIn, Telegram, Discord, and more.
*   **🎛️ Interactive CLI**: Runtime menu to toggle features (Publishing, n8n, etc.) on/off for each session.
*   **🛡️ Robust Scraping**: Uses ScrapingAnt with API key rotation to bypass anti-bot protections.

## 🛠️ Prerequisites

*   Python 3.8+
*   A WordPress Website (with Application Password enabled)
*   ScrapingAnt API Key(s)
*   Google Gemini API Key
*   n8n Instance (Self-hosted or Cloud)

## 🚀 Installation

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/yourusername/amazon-affiliate-bot.git
    cd amazon-affiliate-bot
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Setup Configuration**:
    Create a `.env` file or update `config.py` with your credentials:
    
    *   `GEMINI_API_KEY`: Your Google AI Studio API key.
    *   `WP_URL`: Your WordPress site URL.
    *   `WP_USERNAME`: Your WordPress username.
    *   `WP_APP_PASSWORD`: Application password (Generate in WP Admin > Users).
    *   `SCRAPINGANT_API_KEYS`: List of your scraping keys.

4.  **Prepare Keywords**:
    Add your target keywords (one per line) to `keywords.txt`.
    ```text
    best retro handheld console 2025
    top gaming headset under 50
    ...
    ```

## 🎮 Usage

Run the bot using the main script. It will present an interactive menu to configure the session.

```bash
python main.py
```

**Interactive Menu:**
```text
>>> Configuration Setup
1. Include Comparison Table? (y/n): y
2. Include Internal Links? (y/n): y
3. Publish to WordPress? (y/n): y
4. Trigger n8n Automation (Social Media)? (y/n): y
```

The bot will then:
1.  Pick a keyword from `keywords.txt`.
2.  Scrape Amazon for products.
3.  Check if they already exist in the database.
4.  Generate an article + schema.
5.  Publish to WordPress.
6.  Trigger the n8n workflow.

## 🔗 n8n Workflow Integration

This bot is designed to work with a specific n8n workflow for social syndication.

1.  **Import Workflow**: Import the JSON workflow file (provided separately) into your n8n instance.
2.  **Configure Credentials**: Set up your Pinterest, Facebook, Telegram, etc., credentials in n8n.
3.  **Update Webhook**:
    *   Copy your Production Webhook URL from n8n.
    *   Update `N8N_WEBHOOK_URL` in `n8n_handler.py`.

**Data Sent to n8n:**
*   `title`: Product Title
*   `amazon_link`: Published Post Link
*   `image_url`: Product Image URL
*   `social_caption`: Short generated caption
*   `category`: Niche Keyword
*   `long_description`: Full Article HTML

## 📂 Project Structure

*   `main.py`: Core logic and orchestration.
*   `scraper.py`: Amazon scraping logic with ScrapingAnt.
*   `ai_writer.py`: Gemini AI content generation prompt & logic.
*   `publisher.py`: WordPress REST API handler.
*   `database.py`: SQLite database management.
*   `schema_helper.py`: JSON-LD schema generator.
*   `n8n_handler.py`: Webhook trigger for n8n.
*   `config.py`: Configuration and API keys.

## ⚠️ Disclaimer

This tool is for educational purposes. excessively scraping Amazon may violate their Terms of Service. Use responsibly and ensure you comply with the Amazon Associates Operating Agreement.
