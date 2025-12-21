# Project Context: Amazon Affiliate Automation Bot

## 1. Project Vision
We are building a fully automated "Programmatic SEO" website using Python. The goal is to scrape Amazon product data, generate high-quality, human-like reviews using AI, and automatically publish them to a WordPress site with affiliate links.

## 2. Tech Stack (Strictly Follow This)
* **Language:** Python 3.10+
* **Scraping:** `requests` library with **ScrapingAnt API** (Browser rendering enabled).
* **Database:** `sqlite3` (File: `amazon_products.db`).
* **AI Model:** **Google Gemini API** (`gemini-1.5-flash` model) via `google-generativeai` library.
* **CMS Integration:** WordPress REST API (using `requests`).
* **Scheduling:** The script will eventually run on a VPS via Cron Job.

## 3. Workflow & Architecture
The system consists of 4 main independent modules orchestrated by a main script:

1.  **Scraper (`scraper.py`):**
    * Accepts a product URL or Search Keyword.
    * Uses **ScrapingAnt** to bypass Amazon's anti-bot system.
    * **CRITICAL FEATURE:** Implements an "API Key Rotation" system. We have a list of 10-15 ScrapingAnt tokens. If one token fails (Error 429 or 402), it must automatically switch to the next token.
    * Extracts: Title, Price, Rating, Review Count, Image URL, and ASIN.

2.  **Database Manager (`database.py`):**
    * Uses SQLite.
    * Prevents duplicate entries (ASIN must be UNIQUE).
    * Tracks status: `is_published` (Boolean).

3.  **AI Writer (`ai_writer.py`):**
    * Uses **Google Gemini 1.5 Flash**.
    * Input: Product data from DB.
    * Output: A full HTML-formatted blog post (Title, Intro, Features, Pros/Cons Table, Conclusion).
    * **Style:** Human-like, simple English, short paragraphs. No robotic jargon (e.g., "unleash", "delve").

4.  **Publisher (`publisher.py`):**
    * Connects to WordPress Site.
    * Uploads the product image to WordPress Media Library first.
    * Creates a Post with the generated HTML content and sets the Featured Image.
    * Updates the database `is_published = 1` after success.

## 4. File Structure
Please scaffold the project with this structure:
- `main.py`: The entry point script.
- `config.py`: Stores API Keys (List of ScrapingAnt tokens, Gemini Key, WP Credentials).
- `scraper.py`: Handles scraping logic with rotation.
- `database.py`: Handles DB operations.
- `ai_writer.py`: Handles Gemini prompt and generation.
- `publisher.py`: Handles WordPress uploads.
- `requirements.txt`: List of dependencies.

## 5. Coding Guidelines & Rules
* **Error Handling:** Every API call (Scraping, AI, WordPress) must have `try-except` blocks. If one step fails, log the error but do not crash the whole program.
* **Modularity:** Keep functions small and reusable.
* **Comments:** Add comments explaining the logic, especially for the Key Rotation part.
* **No Selenium:** Do not use Selenium. Use `requests` with ScrapingAnt headers/params.
* **Affiliate Tag:** Ensure the final Amazon link includes a placeholder for the affiliate tag (e.g., `?tag=mytag-20`).

## 6. Immediate Task
Read this context and generate the `requirements.txt`, `config.py` (with placeholder lists), and `database.py` files to start with.