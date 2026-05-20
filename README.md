# 🤖 Whit Logic — Amazon Affiliate Automation Bot

> **একটি সম্পূর্ণ autonomous Amazon affiliate engine** যা নিজে নিজে keyword খোঁজে, Amazon থেকে product scrape করে, Gemini AI দিয়ে SEO-optimized article লেখে এবং whitlogic.online-এ publish করে।

---

## 📋 Table of Contents

- [System Architecture](#-system-architecture)
- [Project Structure](#-project-structure)
- [Prerequisites](#-prerequisites)
- [Environment Setup](#-environment-setup)
- [Database Setup](#-database-setup)
- [Installation](#-installation)
- [Running the Project](#-running-the-project)
- [Bot Workflow (Phase System)](#-bot-workflow-phase-system)
- [Website (Next.js Frontend)](#-website-nextjs-frontend)
- [API Keys Guide](#-api-keys-guide)
- [Troubleshooting](#-troubleshooting)
- [Known Limitations](#-known-limitations)

---

## 🏗 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    WHIT LOGIC PLATFORM                       │
├──────────────────────┬──────────────────────────────────────┤
│   PYTHON BOT (Local) │   NEXT.JS WEBSITE (Vercel)           │
│                      │                                      │
│  ┌──────────────┐    │   ┌─────────────────────────────┐   │
│  │  gui.py      │    │   │  whitlogic.online            │   │
│  │  Streamlit   │    │   │  Next.js 15 + Tailwind CSS  │   │
│  │  Dashboard   │    │   │  Prisma ORM                 │   │
│  └──────┬───────┘    │   └────────────┬────────────────┘   │
│         │            │                │                      │
│  ┌──────▼───────┐    │   ┌────────────▼────────────────┐   │
│  │  main.py     │    │   │  Supabase PostgreSQL         │   │
│  │  Core Bot    │────┼──▶│  • Post table (articles)    │   │
│  │  Controller  │    │   │  • products table (scraped) │   │
│  └──────┬───────┘    │   │  • keyword_pool table       │   │
│         │            │   └─────────────────────────────┘   │
│  ┌──────▼───────┐    │                                      │
│  │ PHASE 0      │    │   ┌─────────────────────────────┐   │
│  │ keyword_     │    │   │  External APIs               │   │
│  │ discoverer   │    │   │  • Gemini AI (article gen)  │   │
│  └──────┬───────┘    │   │  • ScrapingAnt (Amazon)     │   │
│         │            │   │  • Cloudinary (images)      │   │
│  ┌──────▼───────┐    │   │  • YouTube Search API       │   │
│  │  scraper.py  │────┼──▶│                             │   │
│  │  ai_writer   │    │   └─────────────────────────────┘   │
│  │  publisher   │    │                                      │
│  └──────────────┘    │                                      │
└──────────────────────┴──────────────────────────────────────┘
```

---

## 📁 Project Structure

```
Affilieate-Autometion/
│
├── 🤖 BOT CORE
│   ├── main.py                # Main bot controller — orchestrates all phases
│   ├── gui.py                 # Streamlit web dashboard (UI to control bot)
│   ├── config.py              # All config & API key loading from .env
│   │
│   ├── scraper.py             # Amazon product scraper (via ScrapingAnt)
│   ├── ai_writer.py           # Gemini AI article generator with fluff-check
│   ├── publisher.py           # Publishes articles to Next.js website API
│   ├── database.py            # All Supabase REST API interactions
│   ├── keyword_discoverer.py  # Auto keyword discovery (stub — add your logic)
│   │
│   ├── image_composer.py      # Cloudinary image pipeline (800x800 thumbnails)
│   ├── schema_helper.py       # JSON-LD schema generator for SEO
│   ├── seo_utils.py           # Slug generation, meta helpers
│   ├── serp_checker.py        # SERP rank checking utilities
│   ├── keyword_spy.py         # Keyword research helpers
│   ├── make_handler.py        # Make.com webhook integration
│   ├── n8n_handler.py         # n8n social media automation handler
│   │
├── 🌐 WEBSITE (Next.js)
│   └── website/
│       ├── src/app/
│       │   ├── page.tsx                    # Homepage
│       │   ├── watch-reviews/[slug]/       # Dynamic article page
│       │   │   └── page.tsx               # ★ Premium article template
│       │   └── api/                       # Next.js API routes
│       ├── prisma/
│       │   └── schema.prisma              # Database models
│       └── .env.local                     # Website environment variables
│
├── 📄 CONFIG FILES
│   ├── .env                   # Bot environment variables (DO NOT COMMIT)
│   ├── requirements.txt       # Python dependencies
│   ├── keywords.txt           # Manual keyword list (fallback)
│   └── processed_keywords.txt # Tracks processed keywords
│
└── 🛠 UTILITIES
    ├── clean_db_content.py    # One-time DB cleanup script
    └── find_model.py          # Test available Gemini models
```

---

## ✅ Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| **Python** | 3.10+ | Bot runtime |
| **Node.js** | 18+ | Next.js website |
| **Git** | Any | Version control |
| **Supabase account** | Free tier OK | Database |
| **Vercel account** | Free tier OK | Website hosting |
| **Gemini API key** | Free tier available | AI article generation |
| **ScrapingAnt API key** | Paid | Amazon scraping |

---

## 🔐 Environment Setup

### 1. Bot `.env` file (root directory)

`e:\projects\WeeklyProject\Affilieate-Autometion\.env` ফাইলটি এরকম হওয়া উচিত:

```env
# ── Gemini AI API Keys (একাধিক key comma দিয়ে আলাদা করুন) ──
GEMINI_API_KEYS=AIzaSyXXXXXXXXXXXXXXXXXXXXXX,AIzaSyYYYYYYYYYYYYYYYYYYYYYY

# ── ScrapingAnt API Keys (Amazon scraping) ──
SCRAPINGANT_API_KEYS=your_scrapingant_key_here

# ── Supabase Database ──
SUPABASE_URL=https://xxxxxxxxxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# ── Website API (Next.js) ──
NEXT_API_URL=https://whitlogic.online/api/posts
BOT_API_SECRET=your_secret_key_here

# ── Cloudinary (Image Processing) ──
CLOUDINARY_URL=cloudinary://api_key:api_secret@cloud_name

# ── Automation ──
AUTO_KEY=your_automation_trigger_key
```

### 2. Website `.env.local` file

`e:\projects\WeeklyProject\Affilieate-Autometion\website\.env.local`:

```env
# Supabase (Prisma connection)
DATABASE_URL=postgresql://postgres.xxxx:password@aws-0-region.pooler.supabase.com:6543/postgres?pgbouncer=true
DIRECT_URL=postgresql://postgres.xxxx:password@aws-0-region.pooler.supabase.com:5432/postgres

# Bot Authentication
BOT_API_SECRET=your_secret_key_here
```

---

## 🗄 Database Setup

Supabase-এ **৩টি table** থাকতে হবে। Prisma schema থেকে auto-migrate করুন:

```bash
cd website
npx prisma db push
```

অথবা Supabase SQL Editor-এ manually run করুন:

```sql
-- Article posts (Next.js website পড়বে)
CREATE TABLE IF NOT EXISTS "Post" (
  id                  TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
  title               TEXT NOT NULL,
  slug                TEXT UNIQUE NOT NULL,
  content             TEXT NOT NULL,
  "amazonAffiliateLink" TEXT NOT NULL,
  "imageUrl"          TEXT NOT NULL,
  brand               TEXT NOT NULL,
  "modelNumber"       TEXT NOT NULL,
  "createdAt"         TIMESTAMPTZ DEFAULT now(),
  "updatedAt"         TIMESTAMPTZ DEFAULT now()
);

-- Amazon scraped products
CREATE TABLE IF NOT EXISTS products (
  asin          TEXT PRIMARY KEY,
  title         TEXT,
  price         TEXT,
  rating        TEXT,
  review_count  TEXT,
  image_url     TEXT,
  product_url   TEXT,
  is_published  BOOLEAN DEFAULT false,
  post_link     TEXT,
  created_at    TIMESTAMPTZ DEFAULT now()
);

-- Auto keyword pool
CREATE TABLE IF NOT EXISTS keyword_pool (
  id          TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
  keyword     TEXT UNIQUE NOT NULL,
  brand       TEXT,
  "modelNumber" TEXT,
  status      TEXT DEFAULT 'pending',
  "createdAt" TIMESTAMPTZ DEFAULT now()
);
```

> **⚠️ Important:** `keyword_pool` table-এ `id` column **UUID** হতে হবে — `null` constraint error avoid করতে।

---

## 📦 Installation

### Bot (Python)

```bash
# 1. Project directory-তে যান
cd "e:\projects\WeeklyProject\Affilieate-Autometion"

# 2. Virtual environment তৈরি করুন
python -m venv .venv

# 3. Activate করুন (Windows)
.venv\Scripts\activate

# 4. Dependencies install করুন
pip install -r requirements.txt
```

### Website (Next.js)

```bash
# 1. Website directory-তে যান
cd website

# 2. Dependencies install করুন
npm install

# 3. Prisma client generate করুন
npx prisma generate

# 4. Database sync করুন
npx prisma db push
```

---

## 🚀 Running the Project

### ☁️ Bot Dashboard (Streamlit Cloud) — লাইভ সার্ভার (Recommended)

Bot-টি বর্তমানে **Streamlit Cloud**-এ ডিপ্লয় করা আছে। আপনি যেকোনো জায়গা থেকে এটি অ্যাক্সেস করে অটোমেশন কন্ট্রোল করতে পারবেন:

> **🔗 Live Dashboard:** [https://whitlogicautomation.streamlit.app/](https://whitlogicautomation.streamlit.app/)

Dashboard থেকে:
1. **"IGNITE AUTOMATION"** বাটন ক্লিক করুন — bot চালু হবে
2. Real-time logs দেখুন
3. Published articles এবং stats দেখুন

---

### ▶ Local Development (Streamlit GUI)

যদি আপনি আপনার নিজের কম্পিউটারে (Locally) চালাতে চান:

```bash
# Virtual environment activate করুন (যদি না থাকে)
.venv\Scripts\activate

# Streamlit dashboard চালু করুন
streamlit run gui.py
```

Browser-এ যান: **http://localhost:8501**

---

### ▶ Headless Mode (Background / Server)

GUI ছাড়া সরাসরি bot চালাতে:

```bash
python main.py
```

---

### ▶ Website (Local Development)

```bash
cd website
npm run dev
```

Browser-এ যান: **http://localhost:3000**

---

### ▶ Website (Production — Vercel)

```bash
cd website
git add -A
git commit -m "your message"
git push
```

Vercel automatically deploy করবে → **https://whitlogic.online**

---

## ⚙️ Bot Workflow (Phase System)

Bot চালু হলে নিচের phase-গুলো sequential-ভাবে চলে:

```
START
  │
  ▼
[PHASE 0] Keyword Pool Check
  ├─ Supabase keyword_pool-এ pending count করে
  ├─ যদি < 5 keywords → keyword_discoverer.py চালায়
  └─ keywords.txt fallback হিসেবে ব্যবহার করে
  │
  ▼
[PHASE 1] Keyword Processing Loop
  │  প্রতিটি keyword-এর জন্য:
  ├─ Amazon search করে (scraper.py via ScrapingAnt)
  ├─ Product data Supabase-এ save করে (database.py)
  ├─ Gemini AI দিয়ে HTML article generate করে (ai_writer.py)
  │    └─ Fluff-check: 14টি AI buzzword detect & reject করে
  ├─ Cloudinary-তে thumbnail upload করে (image_composer.py)
  └─ whitlogic.online API-তে POST করে publish করে (publisher.py)
  │
  ▼
[COMPLETE] Stats print করে, পরের cycle-এ যায়
```

### Keyword Priority Order:
1. **Supabase `keyword_pool`** (status = 'pending')
2. **`config.py` NICHE_KEYWORDS** list
3. **`keywords.txt`** file (manual fallback)

---

## 🌐 Website (Next.js Frontend)

### Pages:

| Route | Description |
|-------|-------------|
| `/` | Homepage — latest reviews grid |
| `/watch-reviews/[slug]` | Individual article page (premium design) |

### Article Page Features:
- **Cinematic hero** — product image full-width background
- **Reading progress bar** — top-এ amber gradient bar
- **Sticky sidebar** — score bars, Amazon CTA button
- **Verdict card** — dark glass-morphism style
- **JSON-LD Schema** — Article, Product, BreadcrumbList, FAQ
- **Mobile sticky CTA** — bottom-এ floating buy button

### API Endpoints:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/posts` | `POST` | Bot নতুন article publish করে |

**Authentication:** `x-bot-api-secret` header (`.env`-এর `BOT_API_SECRET`)

---

## 🔑 API Keys Guide

### Gemini AI (Google)
1. যান: https://aistudio.google.com/app/apikey
2. **"Create API Key"** ক্লিক করুন
3. `.env`-এর `GEMINI_API_KEYS=` এ paste করুন
4. Multiple keys comma দিয়ে আলাদা করুন (rotation এর জন্য)

**Preferred Models (Priority Order):**
```
gemini-2.5-flash → gemini-1.5-flash → gemini-1.5-pro → gemini-pro
```

### ScrapingAnt
1. যান: https://scrapingant.com
2. Account তৈরি করুন → API key copy করুন
3. `.env`-এর `SCRAPINGANT_API_KEYS=` এ paste করুন

### Supabase
1. যান: https://supabase.com → নতুন project তৈরি করুন
2. **Settings → API** থেকে:
   - `Project URL` → `SUPABASE_URL`
   - `anon public` key → `SUPABASE_KEY`
3. **Settings → Database** থেকে connection string → website `.env.local`

### Cloudinary
1. যান: https://cloudinary.com → free account তৈরি করুন
2. Dashboard থেকে **"API Environment variable"** copy করুন
3. Format: `cloudinary://api_key:api_secret@cloud_name`

---

## 🛠 Troubleshooting

### `UnicodeEncodeError: 'charmap' codec`
**কারণ:** Python file-এ emoji আছে।
```bash
# Auto-fix করুন:
python -c "
import re, sys
sys.stdout.reconfigure(encoding='utf-8')
# ... emoji strip script
"
```
**Status:** ✅ সব Python file-এ already fix করা হয়েছে।

---

### `null value in column 'id' of relation 'keyword_pool'`
**কারণ:** `keyword_pool` table-এ UUID default নেই।
**Fix:** Supabase SQL editor-এ run করুন:
```sql
ALTER TABLE keyword_pool ALTER COLUMN id SET DEFAULT gen_random_uuid()::text;
```

---

### `[ERROR] AI content generation failed`
**কারণ 1:** Gemini API quota শেষ → নতুন key add করুন `.env`-এ।
**কারণ 2:** Response return না হওয়া (indentation bug) → ✅ Already fixed in `ai_writer.py`.

---

### Article page-এ social media JSON text দেখাচ্ছে
**কারণ:** JSON strip regex fail করেছে।
**Fix:** Database cleanup script চালান:
```bash
python clean_db_content.py
```
**Status:** ✅ Already fixed — `ai_writer.py`-এ 4-strategy robust cleaner আছে।

---

### `This page couldn't load` (Vercel)
**কারণ:** Next.js 15-এ `params` এখন `Promise` — await করতে হবে।
**Status:** ✅ Already fixed in `watch-reviews/[slug]/page.tsx`.

---

### Bot keyword খুঁজে পাচ্ছে না
**সমাধান:** Supabase `keyword_pool` table-এ manually keyword add করুন:
```sql
INSERT INTO keyword_pool (keyword, status)
VALUES ('best budget gaming headset 2025', 'pending');
```

---

## ⚠️ Known Limitations

| Limitation | Details |
|-----------|---------|
| **Keyword Discovery** | `keyword_discoverer.py` currently a stub — manual keywords দিতে হবে |
| **ScrapingAnt** | Paid service — free tier limited |
| **Amazon Rate Limiting** | Bot 5s delay দেয় keywords-এর মধ্যে |
| **Gemini deprecated** | `google.generativeai` → ভবিষ্যতে `google.genai` SDK-এ migrate করতে হবে |
| **Single site** | এখন শুধু `whitlogic.online` — multi-site support নেই |

---

## 📊 Database Schema

```
Post (Next.js website reads this)
├── id            : UUID (primary key)
├── title         : String
├── slug          : String (unique, URL-friendly)
├── content       : Text (AI-generated HTML)
├── amazonAffiliateLink : String
├── imageUrl      : String (Cloudinary or Amazon URL)
├── brand         : String
├── modelNumber   : String
├── createdAt     : DateTime
└── updatedAt     : DateTime

products (Bot tracks scraping state)
├── asin          : String (primary key — Amazon product ID)
├── title, price, rating, review_count
├── image_url, product_url
├── is_published  : Boolean
└── post_link     : String (published URL)

keyword_pool (Autonomous keyword management)
├── id            : UUID (primary key)
├── keyword       : String (unique)
├── status        : 'pending' | 'processed' | 'failed'
└── createdAt     : DateTime
```

---

## 🔄 Development Workflow

```bash
# Bot এ কোনো change করলে:
# শুধু Streamlit reload করুন → browser-এ 'R' press করুন

# Website-এ change করলে:
cd website
git add -A
git commit -m "feat: your change"
git push
# Vercel auto-deploy হবে ~2 minutes এ
```

---

## 📞 Quick Reference

| Task | Command |
|------|---------|
| Bot dashboard চালু করুন | `streamlit run gui.py` |
| Bot headless চালান | `python main.py` |
| Website local চালান | `cd website && npm run dev` |
| DB cleanup করুন | `python clean_db_content.py` |
| Available Gemini models দেখুন | `python find_model.py` |
| Prisma DB sync করুন | `cd website && npx prisma db push` |
| Prisma Studio (DB GUI) | `cd website && npx prisma studio` |

---

## 📲 Social Media Automation (Make.com)

আমাদের bot প্রতিটি article publish করার পর **Make.com** webhook-এর মাধ্যমে automatically social media-তে post করে।

### 🔗 Make.com Scenario Template

নতুন করে Make.com scenario তৈরি করতে হলে এই **public template** link ব্যবহার করুন:

> **👉 [Whit Logic — Social Media Auto Publisher Template](https://us2.make.com/public/shared-scenario/iC9JeBLAtXk/integration-webhooks-facebook-pages-in)**

### কীভাবে import করবেন:
1. উপরের link-এ যান
2. **"Use this template"** বা **"Create scenario from template"** click করুন
3. Make.com account-এ login করুন
4. প্রতিটি module-এ নিজের account connect করুন:
   - 📘 Facebook Pages → আপনার Page
   - 📸 Instagram for Business → আপনার IG account
   - 📌 Pinterest → আপনার Board
   - 💼 LinkedIn → আপনার account
5. **Webhook URL** copy করুন → GitHub Secret `MAKE_WEBHOOK_URL` update করুন

### Scenario Structure:
```
[Custom Webhook] → [Router]
                      ├── Facebook Pages → Create a Post
                      ├── Instagram for Business → Create a Photo Post
                      ├── Pinterest → Create a Pin
                      └── LinkedIn → Create a Share Post
```

### Webhook Data Format (bot থেকে যা আসে):
```json
{
  "title": "Article title",
  "url": "https://www.whitlogic.online/article-slug",
  "imageUrl": "https://res.cloudinary.com/dduxtar6i/...",
  "keyword": "product keyword",
  "brand": "Brand Name"
}
```

### GitHub Secrets যা লাগবে:
| Secret | Value |
|--------|-------|
| `MAKE_WEBHOOK_URL` | `https://hook.us2.make.com/ibqcj99b0upzsy1h5ffmqtpo6v544tz3` |
| `CLOUDINARY_URL` | `cloudinary://API_KEY:API_SECRET@CLOUD_NAME` |

---

*Built with ❤️ for autonomous Amazon affiliate monetization — Whit Logic Platform*
