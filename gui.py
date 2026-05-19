import streamlit as st
import pandas as pd
import os
import sys
import time
import base64
import requests

# Fix Windows console emoji charmap encode errors
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import serp_checker
import keyword_spy
from main import main as run_bot
from config import NICHE_KEYWORDS, SCRAPINGANT_API_KEYS, GEMINI_API_KEYS, N8N_WEBHOOK_URL, MAKE_WEBHOOK_URL, SUPABASE_URL, SUPABASE_KEY, NEXT_API_URL, BOT_API_SECRET, AUTO_KEY

# ==========================================
# 🛠️ HELPER FUNCTIONS (SUPABASE REST)
# ==========================================

def get_headers():
    if not SUPABASE_URL or not SUPABASE_KEY:
        return {}
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

def load_sites():
    """Load sites from Supabase via REST."""
    if not SUPABASE_URL:
        st.error("Supabase not connected. Check .env")
        return []
        
    try:
        url = f"{SUPABASE_URL}/rest/v1/sites?select=*&order=id.asc"
        response = requests.get(url, headers=get_headers())
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.error(f"Failed to load sites: {e}")
        return []

def add_site(name, url_link, username, password, n8n):
    """Add a new site to Supabase."""
    if not SUPABASE_URL: return
    try:
        import uuid
        data = {
            "id": str(uuid.uuid4()),
            "name": name,
            "url": url_link,
            "username": username,
            "app_password": password,
            "n8n_webhook": n8n,
            "keywords": []
        }
        url = f"{SUPABASE_URL}/rest/v1/sites"
        headers = get_headers()
        # No conflict resolution needed for new insert usually, unless ID specified
        response = requests.post(url, headers=headers, json=data)
        if response.status_code < 400:
            return True
        st.error(f"API Error: {response.text}")
        return False
    except Exception as e:
        st.error(f"Error adding site: {e}")
        return False

def delete_site(site_id):
    """Delete a site from Supabase."""
    if not SUPABASE_URL: return
    try:
        url = f"{SUPABASE_URL}/rest/v1/sites?id=eq.{site_id}"
        requests.delete(url, headers=get_headers())
        return True
    except Exception as e:
        st.error(f"Error deleting site: {e}")
        return False

def update_site_keywords(site_id, keywords_list):
    """Update keywords for a site."""
    if not SUPABASE_URL: return
    try:
        url = f"{SUPABASE_URL}/rest/v1/sites?id=eq.{site_id}"
        requests.patch(url, headers=get_headers(), json={"keywords": keywords_list})
        return True
    except Exception as e:
        st.error(f"Error updating keywords: {e}")
        return False

def get_base64_video(file_path):
    """Read video file and encode to base64"""
    try:
        with open(file_path, "rb") as f:
            data = f.read()
            return base64.b64encode(data).decode()
    except:
        return None

# ==========================================
# 🎨 PAGE CONFIG & STYLING
# ==========================================
st.set_page_config(page_title="Amazon Affiliate Bot", page_icon="🤖", layout="wide")

# --- 🎨 PROFESSIONAL UI STYLING ---
st.markdown("""
<style>
    /* IMPORT FONTS */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* GLOBAL THEME OVERRIDES */
    .stApp {
        background: #0E1117;
    }
    
    /* CUSTOM GRADIENT BUTTONS */
    div.stButton > button:first-child {
        background: linear-gradient(90deg, #FF4B4B 0%, #FF9000 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    div.stButton > button:first-child:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(255, 75, 75, 0.4);
    }

    /* GLASSMORPHISM CARDS */
    .glass-card {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 20px;
        transition: border 0.3s ease;
        margin-bottom: 20px;
    }
    .glass-card:hover {
        border: 1px solid rgba(255, 255, 255, 0.2);
    }

    /* HEADER STYLES */
    .app-header {
        text-align: center;
        padding: 40px 0 20px 0;
        background: radial-gradient(circle at center, rgba(255, 75, 75, 0.1) 0%, transparent 70%);
    }
    .app-title {
        font-size: 3rem;
        font-weight: 800;
        background: -webkit-linear-gradient(0deg, #FFFFFF, #AAAAAA);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -1px;
    }
    .app-subtitle {
        color: #666;
        font-size: 1.1rem;
        margin-top: -10px;
    }
    
    /* TAB STYLING */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 8px;
        color: #888;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background-color: rgba(255, 255, 255, 0.05);
        color: #fff;
    }
    
    /* MATRIX TERMINAL LOGS */
    .stCodeBlock {
        border-right: 2px solid #0f0 !important;
    }
    .stCodeBlock pre {
        background-color: #000 !important;
        border: 1px solid #00ff41 !important;
    }
    .stCodeBlock code {
        color: #00ff41 !important;
        font-family: 'Courier New', monospace !important;
        text-shadow: 0 0 5px rgba(0, 255, 65, 0.5);
    }

    /* HIDE STREAMLIT CHROME (Sidebar & Header) */
    [data-testid="stSidebar"] {
        display: none;
    }
    [data-testid="stHeader"] {
        background: transparent;
        visibility: hidden;
    }
    #MainMenu {
        visibility: hidden;
    }
    footer {
        visibility: hidden;
    }

    /* REMOVE TOP PADDING & MARGIN */
    .block-container {
        padding-top: 0rem !important;
        margin-top: 0rem !important;
    }

    /* STICKY TABS */
    .stTabs [data-baseweb="tab-list"] {
        position: sticky;
        top: 0;
        z-index: 9999;
        background-color: #0E1117; /* Match app background */
        padding-top: 10px;
        padding-bottom: 10px;
        margin-top: 0px;
        border-bottom: 1px solid rgba(255,255,255,0.1);
    }
</style>
""", unsafe_allow_html=True)

# --- APP HEADER (Removed by User Request) ---
# st.markdown... removed


# ==========================================
# 🤖 AUTOMATION TRIGGER (MAGIC LINK)
# ==========================================
# Link format: /?start=true&key=SECRET&site_id=1
query_params = st.query_params
if query_params.get("start") == "true":
    secret = query_params.get("key")
    if secret == AUTO_KEY:
        st.write("🤖 Automation Triggered via URL...")
        
        # Load sites to find target
        sites = load_sites()
        if not sites:
            st.error("❌ No sites configured in Supabase.")
            st.stop()
            
        # Target specific site or default to first
        target_site = sites[0]
        if query_params.get("site_id"):
            try:
                sid = int(query_params.get("site_id"))
                target_site = next((s for s in sites if s['id'] == sid), sites[0])
            except:
                pass
        
        st.write(f"🌍 Target Site: {target_site['name']} ({target_site['url']})")
        
        # Default Automation Config
        auto_config = {
            'max_keywords': 1,             # Process 1 keyword per run (ideal for cron)
            'products_per_keyword': 3,
            'max_total_articles': 3,
            'use_comparison': True,
            'use_internal_links': True,
            'publish_wp': True,
            'trigger_n8n': True,
            'delay_between_products': 2,
            'delay_between_keywords': 2
        }
        
        try:
            stats = run_bot(config=auto_config, log_function=st.write, site_config=target_site)
            st.success(f"✅ Run Complete: {stats['articles_published']} Published")
        except Exception as e:
            st.error(f"❌ Automation Error: {e}")
            
        st.stop() # 🛑 STOP GUI RENDERING HERE
    else:
        st.error("⛔ Invalid Security Key")
        
        # DEBUGGING INFO
        if not AUTO_KEY:
            st.error("⚠️ CRITICAL ERROR: `AUTO_KEY` is NOT SET in the Server Environment Variables!")
            st.info("Please go to Render Dashboard -> Environment -> Add `AUTO_KEY`.")
        else:
            st.warning(f"Debug: Received '{secret}' but expected '{AUTO_KEY}'")
            
        st.stop()

# ==========================================
# 🎨 PREMIUM SAAS UI (Glassmorphism & 3D)
# ==========================================
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
    /* --- GLOBAL THEME --- */
    :root {
        --primary-gradient: linear-gradient(135deg, #00C9FF 0%, #92FE9D 100%);
        --glass-bg: rgba(255, 255, 255, 0.05);
        --glass-border: 1px solid rgba(255, 255, 255, 0.1);
        --neon-blue: #00f3ff;
        --neon-purple: #bc13fe;
    }
    
    .stApp {
        background: radial-gradient(circle at top left, #1b003a, #0c0c1e, #000000);
        font-family: 'Outfit', sans-serif;
    }

    h1, h2, h3, .stText, p, div {
        color: #ffffff;
        font-family: 'Outfit', sans-serif !important;
    }

    /* --- FROSTED GLASS SIDEBAR --- */
    section[data-testid="stSidebar"] {
        background: rgba(255, 255, 255, 0.05); /* Increased visibility */
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-right: 1px solid rgba(255, 255, 255, 0.08);
    }
    
    /* --- 3D HOVER CARDS (Columns as Cards) --- */
    /* Targeting columns inside the main dashboard tabs to look like cards */
    div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
        background: var(--glass-bg);
        backdrop-filter: blur(12px);
        border: var(--glass-border);
        border-radius: 20px;
        padding: 20px;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    }
    
    div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:hover {
        transform: translateY(-5px) scale(1.01);
        box-shadow: 0 20px 40px rgba(0,0,0,0.4), 0 0 20px rgba(0, 243, 255, 0.2);
        border-color: rgba(255, 255, 255, 0.3);
    }

    /* --- NEON ACCENTS: SLIDERS --- */
    div[data-baseweb="slider"] div[data-testid="stTickBar"] {
        background: transparent;
    }
    div[data-baseweb="slider"] div[role="slider"] {
        background-color: var(--neon-blue) !important;
        box-shadow: 0 0 10px var(--neon-blue);
    }
    div[data-baseweb="slider"] div {
        background: linear-gradient(90deg, var(--neon-purple), var(--neon-blue));
    }

    /* --- GLOWING BUTTONS --- */
    .stButton>button {
        background: linear-gradient(90deg, #FF3CAC 0%, #784BA0 50%, #2B86C5 100%);
        background-size: 200% auto;
        color: white !important;
        border: none;
        border-radius: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: all 0.4s ease;
        box-shadow: 0 0 15px rgba(120, 75, 160, 0.5);
    }
    .stButton>button:hover {
        background-position: right center;
        transform: scale(1.03);
        box-shadow: 0 0 25px rgba(120, 75, 160, 0.8);
    }

    /* --- GLASS TABS/NAVBAR (FLOATING DOCK) --- */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(0, 0, 0, 0.3);
        border-radius: 60px;
        padding: 10px 15px;
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        display: inline-flex;
        margin-bottom: 30px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        color: #aaaaaa;
        border: none;
        border-radius: 40px;
        padding: 8px 30px;
        font-weight: 600;
        font-size: 16px;
        transition: all 0.3s ease;
        margin: 0 5px;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        color: white;
        background: rgba(255, 255, 255, 0.1);
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(90deg, #FF3CAC 0%, #784BA0 100%);
        color: white !important;
        box-shadow: 0 0 20px rgba(120, 75, 160, 0.6);
        border: none;
        transform: scale(1.05);
    }

    /* --- INPUTS --- */
    .stTextInput>div>div>input {
        background: rgba(0,0,0,0.3) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        color: white !important;
        border-radius: 10px;
    }
    .stTextInput>div>div>input:focus {
        border-color: var(--neon-blue) !important;
        box-shadow: 0 0 10px rgba(0, 243, 255, 0.3);
    }

    /* HIDE DEFAULT STREAMLIT ELEMENTS */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    /* header visibility removed to show sidebar toggle */
</style>
""", unsafe_allow_html=True)

# 🎥 Background Video
video_path = os.path.join("assets", "background video.mp4")
if os.path.exists(video_path):
    video_b64 = get_base64_video(video_path)
    if video_b64:
        st.markdown(f"""
        <style>
            .stApp {{ background: transparent; }}
            .video-background {{
                position: fixed; right: 0; bottom: 0;
                min-width: 100%; min-height: 100%;
                width: 100vw; height: 100vh;
                z-index: -1; object-fit: fill; opacity: 0.6;
            }}
        </style>
        <video autoplay muted loop playsinline class="video-background">
            <source src="data:video/mp4;base64,{video_b64}" type="video/mp4">
        </video>
        """, unsafe_allow_html=True)
else:
    st.markdown("""<style>.stApp { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); }</style>""", unsafe_allow_html=True)

# ==========================================
# 🧠 CONFIG & NAVIGATION
# ==========================================
sites = load_sites()

# --- INJECT DEFAULT SITE FROM .ENV (WHIT LOGIC) IF MISSING ---
default_site_name = "Whit Logic"
has_default = any(s.get('name') == default_site_name for s in sites)

# -------------------------------------------------------------

# Hide Sidebar (CSS) or just keep it empty/minimal
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/4712/4712035.png", width=50)
    st.caption("v2.5 Cloud")

# ==========================================
# 🚀 MAIN DASHBOARD
# ==========================================
# Title removed by user request

if not sites:
    st.warning("⚠️ No sites configured. Please add a site in the 'Site Manager' tab.")
    # We allow rendering so they can see the tab to add a site
    # But selected_site logic might fail.
    # We'll fix selected_site check below.

# TABS ARE THE NAVIGATION BAR
# TABS ARE THE NAVIGATION BAR
tab1, tab2, tab3, tab_bot, tab_analytics, tab_serp, tab4, tab5 = st.tabs(["📊 Live Monitor", "🌍 Site Manager", "📝 Keywords", "🤖 Bot Engine", "📈 Analytics", "🔍 SERP", "💾 Cloud DB", "🔧 Tools"])

# --- TAB 2: SITE MANAGER (Logic runs FIRST to define variables) ---
with tab2:
    st.subheader("🌍 Manage Sites & Settings")
    
    # 1. SITE SELECTOR & GLOBAL CONFIG
    c_sel, c_conf = st.columns([1, 1])
    
    with c_sel:
        st.markdown("### 🎯 Target Selection")
        site_names = [s['name'] for s in sites] if sites else []
        selected_site_idx = 0
        if 'last_selected_site' in st.session_state and site_names:
            if st.session_state.last_selected_site in site_names:
                selected_site_idx = site_names.index(st.session_state.last_selected_site)

        if site_names:
            selected_site_name = st.selectbox("Active Website:", site_names, index=selected_site_idx)
            st.session_state.last_selected_site = selected_site_name
            selected_site = next((s for s in sites if s['name'] == selected_site_name), sites[0])
        else:
            selected_site = None
            st.error("No sites available.")

    with c_conf:
        st.markdown("### ⚙️ Global Defaults")
        # Global variables used in Dashboard
        c1, c2 = st.columns(2)
        with c1:
            max_keywords = st.number_input("Global KW Limit", 1, 50, 1)
            products_per_keyword = st.number_input("Global Prod/KW", 1, 10, 1)
        with c2:
            max_total_articles = st.number_input("Global Max Arts", 0, 100, 1)
            # Toggles
            c3, c4 = st.columns(2)
            use_comparison = c3.toggle("Comparison", False)
            use_internal_links = c4.toggle("Inter-Links", True)
            publish_wp = c3.toggle("Publish WP", True)
            trigger_n8n = c4.toggle("n8n Trig", True)
            
            # Default Delays (Hidden/Advanced or just here?)
            # User simplified them in Dashboard, but we need definitions here if Dashboard uses them as defaults.
            # We'll init them here.
            delay_products = 2
            delay_keywords = 5
            interval_minutes = st.number_input("Sched Interval (m)", 0, 1440, 0, help="0 = Instant Publish")
            
    st.divider()
    
    # 2. ADD / DELETE SITES
    with st.expander("➕ Add / 🗑️ Delete Sites", expanded=True):
        col_add, col_del = st.columns(2)
        
        with col_add:
            st.markdown("#### Add New Site")
            with st.form("add_site_form_tab"):
                new_name = st.text_input("Site Name (e.g. Whitlogic)")
                new_url = st.text_input("Next.js Site URL (e.g. https://www.whitlogic.online)")
                new_pass = st.text_input("Bot API Secret (Required for publishing)", type="password")
                new_n8n = st.text_input("Make.com Webhook (Optional)")
                
                if st.form_submit_button("Add Site"):
                    if new_name and new_url:
                        # Passing empty string for username since Next.js only needs the secret
                        if add_site(new_name, new_url, "", new_pass, new_n8n):
                            st.success("Site Added!")
                            st.rerun()
        
        with col_del:
            st.markdown("#### Existing Sites")
            if sites:
                for site in sites:
                    c1, c2 = st.columns([3, 1])
                    c1.text(f" {site['name']}")
                    if c2.button("🗑️", key=f"del_tab_{site['id']}"):
                        if delete_site(site['id']):
                            st.rerun()
            else:
                st.info("No sites found.")


# --- TAB 1: LIVE MONITOR (Logic runs SECOND) ---
# --- TAB 1: LIVE MONITOR ---
with tab1:
    
    # --- QUICK SITE SWITCHER ---
    if sites:
        c_switch, c_info = st.columns([1, 2])
        with c_switch:
            site_opts = [s['name'] for s in sites]
            # Determine current index safely
            curr_idx = 0
            if selected_site and selected_site['name'] in site_opts:
                curr_idx = site_opts.index(selected_site['name'])
            
            # Switcher
            new_site_name = st.selectbox("🔹 Active Site:", site_opts, index=curr_idx, key="t1_site_sel")
            
            # Helper to sync Update
            if selected_site and new_site_name != selected_site['name']:
                st.session_state.last_selected_site = new_site_name
                st.rerun()
                
        with c_info:
            if selected_site:
                 st.caption("Active Target URL")
                 st.code(selected_site['url'], language="text")
            else:
                 st.error("No Site Selected")

    if not selected_site:
        st.error("Please select or add a site in 'Site Manager' tab.")
        st.stop()

    
    # --- 0. LOGGER SETUP ---
    if 'system_logs' not in st.session_state:
        st.session_state.system_logs = []

    # Placeholder for logs
    # ----------------------------------
    # 1. METRICS SECTION (TOP)
    # ----------------------------------
    
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown("""
        <div class="glass-card">
            <h4 style="margin:0; color:#888; font-size:12px; text-transform:uppercase; letter-spacing:1px;">Products Scraped</h4>
            <h2 style="margin:5px 0 0 0; color:#FF9900; font-size:32px;">1,247</h2>
            <p style="margin:5px 0 0 0; color:#00ff88; font-size:12px;">⬆ 12.5% vs avg</p>
        </div>
        """, unsafe_allow_html=True)
    with m2:
        st.markdown("""
        <div class="glass-card">
            <h4 style="margin:0; color:#888; font-size:12px; text-transform:uppercase; letter-spacing:1px;">Live Articles</h4>
            <h2 style="margin:5px 0 0 0; color:#00C9FF; font-size:32px;">342</h2>
            <p style="margin:5px 0 0 0; color:#00ff88; font-size:12px;">⬆ 8.3% this week</p>
        </div>
        """, unsafe_allow_html=True)
    with m3:
        st.markdown("""
        <div class="glass-card">
            <h4 style="margin:0; color:#888; font-size:12px; text-transform:uppercase; letter-spacing:1px;">Database Size</h4>
            <h2 style="margin:5px 0 0 0; color:#A76DFF; font-size:32px;">2,891</h2>
            <p style="margin:5px 0 0 0; color:#00ff88; font-size:12px;">Healthy</p>
        </div>
        """, unsafe_allow_html=True)
    with m4:
        st.markdown("""
        <div class="glass-card">
            <h4 style="margin:0; color:#888; font-size:12px; text-transform:uppercase; letter-spacing:1px;">Conversion Rate</h4>
            <h2 style="margin:5px 0 0 0; color:#FF4B4B; font-size:32px;">3.8%</h2>
            <p style="margin:5px 0 0 0; color:#00ff88; font-size:12px;">⬆ 2.1% optimize</p>
        </div>
        """, unsafe_allow_html=True)
    st.divider()

    # ----------------------------------
    # 2. CONTROLS SECTION (MIDDLE)
    # ----------------------------------
    c_ignite, c_controls = st.columns([1, 1.5])
    
    with c_ignite:
        st.markdown("""
        <div class="glass-card" style="text-align: center; height: 100%; display: flex; flex-direction: column; justify-content: center;">
            <h3 style="margin-bottom: 20px; font-weight:700;">🔥 IGNITION CORE</h3>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        # MAIN ACTION BUTTON
        start_btn = st.button("⚡ IGNITE AUTOMATION", use_container_width=True, type="primary")

        # PHASE 0 DISCOVERY BUTTON
        st.markdown("<br>", unsafe_allow_html=True)
        discover_btn = st.button("⚡ Force Trigger Keyword Discovery", use_container_width=True)
        
        if discover_btn:
            try:
                import keyword_discoverer
                st.toast("🔍 Starting Keyword Discovery...", icon="⏳")
                with st.spinner("Discovering low-competition keywords..."):
                    new_kws = keyword_discoverer.discover_watch_keywords(limit=10)
                if new_kws:
                    st.success(f"Added {len(new_kws)} new keywords to the pool!")
                    st.balloons()
                else:
                    st.info("No new keywords found.")
            except Exception as e:
                st.error(f"Error during discovery: {e}")

    with c_controls:
        # Toggles for Automation Settings (Restored)
        t1, t2 = st.columns(2)
        with t1:
            enable_internal_links = st.toggle("Internal Links", value=True)
            auto_publish_wp = st.toggle("Publish to Next.js", value=True)
        with t2:
            enable_n8n = st.toggle("Make.com Trig", value=True)
            enable_comparison = st.toggle("Comparison Table", value=False)
            
        st.divider()

        # Numeric Inputs
        d1, d2 = st.columns(2)
        with d1:
            # Reusing the global variables but allowing local override visually if needed
            # But here I'm correctly mapping inputs
            products_per_keyword = st.number_input("Products/Keyword", 1, 10, products_per_keyword)
        with d2:
            max_total_articles = st.number_input("Max Articles", 1, 50, max_total_articles)
            
        d3, d4 = st.columns(2)
        with d3:
            delay_products = st.number_input("Delay: Products (s)", 0, 300, delay_products)
        with d4:
            delay_keywords = st.number_input("Delay: Keywords (s)", 0, 300, delay_keywords)
        
        # Language Selector
        target_language = st.selectbox("🌐 Target Language", ["English", "Spanish", "French", "German", "Bengali"], index=0)
        
        # Competitor Spy
        competitor_url = st.text_input("🕵️ Competitor URL (Skyscraper Mode)", placeholder="Optional: URL to outrank")
        
        st.caption("📅 Schedule")
        interval_minutes = st.number_input("Publish Interval (mins)", 0, 1440, interval_minutes, help="Time between posts. 0 = Publish Now.")

    # Logs moved to top for realtime updates
    st.divider()

    # ----------------------------------
    # 3. LOGS SECTION (BOTTOM as requested)
    # ----------------------------------
    st.markdown("### 📜 Live Execution Logs")
    
    # Init Logger Container
    log_area = st.empty()
    
    # Initialize session state for logs if not exists
    if 'log_lines' not in st.session_state:
        st.session_state.log_lines = []

    # Function to render logs
    def render_logs():
        if st.session_state.log_lines:
            log_content = "\n".join(st.session_state.log_lines)
            log_area.code(log_content, language="bash")
        
    # Render initial state
    render_logs()

    # Logic Handler
    if start_btn:
        st.toast("🔥 Ignition Sequence Started!", icon="🚀")
        
        # Define config dict for run_bot
        config = {
            'max_keywords': 9999, # Loop until max_articles
            'products_per_keyword': products_per_keyword,
            'max_total_articles': max_total_articles,
            'use_comparison': enable_comparison,
            'use_internal_links': enable_internal_links,
            'publish_nextjs': auto_publish_wp,
            'trigger_n8n': enable_n8n,
            'delay_between_products': delay_products,
            'delay_between_keywords': delay_keywords,
            'interval_minutes': interval_minutes,
            'interval_minutes': interval_minutes,
            'language': target_language,
            'competitor_url': competitor_url
        }

        with st.status("🤖 Bot is running...", expanded=True) as status:
            try:
                # Pass log_container=log_area to run_bot if supported, 
                # OR rely on log_to_gui wrapper availability.
                # Since log_to_gui is defined globally or we need to pass it.
                # run_bot signature needs checking. 
                # Assuming run_bot takes `log_header` or we pass a custom log function.
                # The previous code used `log_function=log_to_gui`.
                
                # We need to redefine log_to_gui here to use our new log_area?
                # No, better: pass the container itself if run_bot supports it, 
                # OR use a closure.
                
                def gui_logger(msg):
                    timestamp = time.strftime("%H:%M:%S")
                    st.session_state.log_lines.append(f"[{timestamp}] {msg}")
                    if len(st.session_state.log_lines) > 50: 
                        st.session_state.log_lines.pop(0)
                    render_logs()
                
                stats = run_bot(config=config, log_function=gui_logger, site_config=selected_site)
                
                status.update(label="✅ Run Complete!", state="complete")
                st.success(f"Published: {stats['articles_published']}")
                if stats['articles_published'] > 0: st.balloons()    
            except Exception as e:
                status.update(label="❌ Failed", state="error")
                st.error(f"Error: {e}")
                st.exception(e)

# --- TAB 2: KEYWORDS ---
with tab2:
    st.subheader(f"📝 Manage Keywords for: {selected_site['name']}")
    
    current_kws = selected_site.get('keywords', []) or []
    current_kw_text = "\n".join(current_kws)
    
    new_kw_text = st.text_area("One keyword per line", value=current_kw_text, height=300, key=f"kws_{selected_site['id']}")
    
    if st.button("💾 Save to Cloud"):
        updated_kws = [line.strip() for line in new_kw_text.split('\n') if line.strip()]
        if update_site_keywords(selected_site['id'], updated_kws):
            st.toast("Saved to Supabase!", icon="☁️")
            time.sleep(1)
            st.rerun()
            st.rerun()

# --- TAB ANALYTICS: WORDPRESS STATS ---
with tab_analytics:
    st.subheader(f"📈 Analytics: {selected_site['name']}")
    
    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    
    if st.button("🔄 Fetch WP Data"):
        if selected_site and selected_site.get('url'):
            try:
                with st.spinner("Talking to WordPress..."):
                    # Basic Auth
                    auth = requests.auth.HTTPBasicAuth(selected_site['username'], selected_site['app_password'])
                    api_url = f"{selected_site['url']}/wp-json/wp/v2/posts?per_page=20&context=edit"
                    
                    response = requests.get(api_url, auth=auth)
                    
                    if response.status_code == 200:
                        posts = response.json()
                        df_posts = pd.DataFrame(posts)
                        
                        # Process Data
                        if not df_posts.empty:
                            total_posts = len(df_posts)
                            published = len(df_posts[df_posts['status'] == 'publish'])
                            scheduled = len(df_posts[df_posts['status'] == 'future'])
                            
                            col_kpi1.metric("Fetched Posts", total_posts)
                            col_kpi2.metric("Live", published)
                            col_kpi3.metric("Scheduled", scheduled)
                            
                            st.divider()
                            st.caption("Recent Activity")
                            
                            # Simplify Table
                            display_data = []
                            for p in posts:
                                display_data.append({
                                    "Title": p['title']['rendered'],
                                    "Date": p['date'],
                                    "Status": p['status'],
                                    "Link": p['link']
                                })
                            st.dataframe(display_data, use_container_width=True)
                        else:
                            st.info("No posts found.")
                    else:
                        st.error(f"WP API Error: {response.status_code}")
            except Exception as e:
                st.error(f"Connection Error: {e}")



# --- TAB SERP: GOOGLE RANK TRACKER + SPY ---
with tab_serp:
    st.subheader("🕵️ Spy Tools & Rank Tracker")
    
    spy_tab1, spy_tab2 = st.tabs(["🔍 Check Rank", "🕵️ Keyword Spy"])
    
    # SUB-TAB 1: RANK TRACKER
    with spy_tab1:
        st.info("Check Google Ranking (US Region)")
        c1, c2 = st.columns([3, 1])
        with c1:
            serp_kw = st.text_input("Ref Keyphrase", placeholder="e.g. best gaming laptop")
            serp_dom = st.text_input("Your Domain", value=selected_site['url'] if sites and selected_site else "")
        with c2:
            st.write("")
            st.write("")
            check_btn = st.button("Check Position", use_container_width=True)
            
        if check_btn and serp_kw and serp_dom:
            with st.status("Checking...", expanded=True):
                rank, url = serp_checker.check_rank(serp_kw, serp_dom)
                if rank:
                    st.success(f"Rank #{rank}")
                    st.code(url)
                else:
                    st.error("Not found in top 100")

    # SUB-TAB 2: KEYWORD SPY
    with spy_tab2:
        st.info("Steal Keywords from Competitors. Enter a category Page URL.")
        spy_url = st.text_input("Competitor URL", placeholder="https://theverge.com/best-laptops")
        
        if st.button("🕵️ Spy Now"):
            if not spy_url:
                st.warning("Enter a URL")
            else:
                with st.status("🔎 Analysing competitor content...", expanded=True):
                    st.write("Scraping page...")
                    result = keyword_spy.scrape_and_extract_keywords(spy_url)
                    
                    if "error" in result:
                        st.error(result['error'])
                    else:
                        st.success(f"Found {result['headings_count']} headings. AI extracted:")
                        st.session_state['spy_keywords'] = result['keywords'] # Store in session
        
        # Display results if they exist in session state
        if 'spy_keywords' in st.session_state and st.session_state['spy_keywords']:
            spy_keywords = st.session_state['spy_keywords']
            st.write("### 💎 Hidden Keywords Found:")
            
            # Create a form to add them
            with st.form("add_spy_kws"):
                selected_spy_kws = []
                # Dynamic checkbox creation
                cols = st.columns(2)
                for i, kw in enumerate(spy_keywords):
                    with cols[i % 2]:
                        if st.checkbox(kw, value=True, key=f"spy_{i}"):
                            selected_spy_kws.append(kw)
                
                add_spy = st.form_submit_button("➕ Add Selected to Queue")
                
                if add_spy:
                    current = selected_site.get('keywords', []) or []
                    # Merge unique (case insensitive check?) - Set is easiest
                    updated = list(set(current + selected_spy_kws))
                    
                    if update_site_keywords(selected_site['id'], updated):
                        st.toast(f"Added {len(selected_spy_kws)} keywords!", icon="✅")
                        # Clear session state to reset spy view
                        del st.session_state['spy_keywords']
                        time.sleep(1)
                        st.rerun()

# --- TAB 3: DATABASE ---
with tab3:
    st.subheader("Product Database (Supabase)")
    if st.button("🔄 Refresh Cloud Data"):
        if SUPABASE_URL:
            try:
                # Fetch recent products from Supabase via REST
                url = f"{SUPABASE_URL}/rest/v1/products?select=title,asin,price,is_published,created_at&order=created_at.desc&limit=50"
                response = requests.get(url, headers=get_headers())
                if response.status_code == 200:
                    df = pd.DataFrame(response.json())
                    st.dataframe(df, use_container_width=True)
                else:
                    st.error(f"API Error: {response.text}")
            except Exception as e:
                st.error(f"Fetch error: {e}")
        else:
            st.warning("Not connected.")

# --- TAB 4: TOOLS ---
with tab4:
    st.subheader(f"🔧 Webhook Tester")
    from n8n_handler import trigger_n8n_workflow
    
    active_webhook = selected_site.get("n8n_webhook") or N8N_WEBHOOK_URL
    st.caption(f"Targeting: `{active_webhook}`")
    
    c1, c2 = st.columns(2)
    with c1:
        t_title = st.text_input("Title", "Test Product")
    with c2:
        t_url = st.text_input("Link", "http://example.com")
        
    if st.button("📡 Send Ping"):
        with st.spinner("Sending..."):
            ret = trigger_n8n_workflow(t_title, t_url, "https://via.placeholder.com/150", "Cap", "Test", "<h1>Desc</h1>", active_webhook)
            if ret: st.success("Sent!")
            else: st.error("Failed")
# --- TAB 8: BOT ENGINE ---
with tab_bot:
    bot_col1, bot_col2 = st.columns(2, gap="large")

    with bot_col1:
        st.markdown("### 🚀 Auto-Pilot Mode")
        st.caption("Fetches next pending keyword from `keyword_pool` table and runs the full pipeline.")
        
        if SUPABASE_URL:
            try:
                count_url = f"{SUPABASE_URL}/rest/v1/keyword_pool?status=eq.pending&select=count"
                count_r = requests.get(count_url, headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Prefer": "count=exact"})
                pending_count = count_r.headers.get("content-range", "?/?").split("/")[-1]
                st.metric("Pending in Queue", pending_count)
            except:
                pass

        if st.button("▶️ Run Next Pending Keyword", type="primary", use_container_width=True):
            if not SUPABASE_URL:
                st.error("❌ Supabase not connected.")
            else:
                try:
                    kp_url = f"{SUPABASE_URL}/rest/v1/keyword_pool?status=eq.pending&select=*&limit=1"
                    kp_r = requests.get(kp_url, headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"})
                    kw_data = kp_r.json()
                    if kw_data:
                        kw = kw_data[0]
                        bot_logs = []
                        with st.status("🤖 Pipeline running...", expanded=True) as status:
                            bot_run_pipeline(
                                keyword=kw['keyword'],
                                brand=kw.get('brand', 'Unknown'),
                                model_num=kw.get('modelNumber', 'Unknown'),
                                log_fn=lambda m: (bot_logs.append(m), st.write(m))
                            )
                            patch_url = f"{SUPABASE_URL}/rest/v1/keyword_pool?id=eq.{kw['id']}"
                            requests.patch(patch_url, headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}, json={"status": "processed"})
                            status.update(label="✅ Done!", state="complete")
                    else:
                        st.info("📭 No pending keywords. Add some below!")
                except Exception as e:
                    st.error(f"Pipeline error: {e}")

        st.divider()
        st.markdown("#### 🔍 Keyword Discoverer (Auto-Queue)")
        seeds = st.text_area("Seed Keywords (one per line)", value="SKMEI tactical watch\\nCURREN military watch")
        if st.button("🔎 Discover & Queue", use_container_width=True):
            st.warning("Keyword Discoverer logic needs to be migrated from automation-bot (coming soon). For now, manually add to Supabase.")

    with bot_col2:
        st.markdown("### ✍️ Manual Mode")
        st.caption("Manually specify a watch to scrape, generate, and publish instantly.")
        with st.form("bot_manual_form"):
            m_keyword = st.text_input("Amazon Search Keyword", placeholder="e.g. SKMEI 2049 tactical watch review")
            m_brand = st.selectbox("Brand", ["SKMEI", "CURREN", "CASIO", "NAVIFORCE", "Other"])
            m_brand_other = st.text_input("If 'Other', type brand name:")
            m_model = st.text_input("Model Number", placeholder="e.g. 2049")
            submitted = st.form_submit_button("🚀 Generate & Publish", type="primary", use_container_width=True)

        if submitted:
            final_brand = m_brand_other.strip() if m_brand == "Other" and m_brand_other.strip() else m_brand
            if not m_keyword.strip() or not m_model.strip():
                st.error("❌ Enter keyword and model number.")
            else:
                with st.status(f"🚀 Running pipeline for {final_brand} {m_model}...", expanded=True) as status:
                    bot_run_pipeline(keyword=m_keyword.strip(), brand=final_brand, model_num=m_model.strip(), log_fn=st.write)
                    status.update(label="✅ Complete!", state="complete")

    st.divider()
    st.markdown("#### 📋 Recently Published Reviews")
    if st.button("🔄 Refresh"):
        if SUPABASE_URL:
            try:
                p_url = f"{SUPABASE_URL}/rest/v1/Post?select=title,brand,modelNumber,slug,createdAt&order=createdAt.desc&limit=20"
                p_r = requests.get(p_url, headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"})
                if p_r.status_code == 200 and p_r.json():
                    posts_df = pd.DataFrame(p_r.json())
                    posts_df["Live Link"] = posts_df["slug"].apply(lambda s: f"https://whitlogic.online/watch-reviews/{s}")
                    st.dataframe(posts_df[["title", "brand", "modelNumber", "createdAt", "Live Link"]], use_container_width=True)
                else:
                    st.info("No published posts found.")
            except Exception as e:
                st.error(e)


# ==========================================
# KEYWORD MANAGER SECTION
# ==========================================
st.divider()
st.markdown("""
<div style='background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
     border: 1px solid rgba(255,144,0,0.3); border-radius: 16px; padding: 24px; margin-top: 16px;'>
<h2 style='color: #FF9000; margin:0 0 4px 0; font-size: 1.4rem;'>Keyword Manager</h2>
<p style='color: #888; margin:0; font-size: 14px;'>Supabase keyword_pool table-এ সরাসরি keyword add, view ও delete করুন</p>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

kw_col1, kw_col2 = st.columns([1, 1], gap="large")

# ── LEFT: Add Keywords ──
with kw_col1:
    st.markdown("##### ➕ Keyword Add করুন")

    # Single keyword
    with st.form("single_kw_form", clear_on_submit=True):
        single_kw = st.text_input(
            "Keyword লিখুন",
            placeholder="e.g. best budget smartwatch under $50"
        )
        kw_brand = st.text_input("Brand (optional)", placeholder="e.g. Casio")
        kw_model = st.text_input("Model (optional)", placeholder="e.g. G-Shock GA-100")
        add_single = st.form_submit_button("Add Keyword", use_container_width=True)

    if add_single and single_kw.strip():
        if SUPABASE_URL:
            import uuid as _uuid
            payload = {
                "id": str(_uuid.uuid4()),
                "keyword": single_kw.strip(),
                "status": "pending"
            }
            if kw_brand.strip():
                payload["brand"] = kw_brand.strip()
            if kw_model.strip():
                payload["modelNumber"] = kw_model.strip()
            h = {
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "return=representation"
            }
            r = requests.post(
                f"{SUPABASE_URL}/rest/v1/keyword_pool",
                headers=h, json=payload
            )
            if r.status_code in [200, 201]:
                st.success(f"Added: **{single_kw.strip()}**")
            elif "unique" in r.text.lower() or "23505" in r.text:
                st.warning("Already exists in pool.")
            else:
                st.error(f"Error: {r.text[:120]}")

    st.markdown("---")
    st.markdown("##### 📋 Bulk Import (একসাথে অনেক keyword)")
    bulk_text = st.text_area(
        "প্রতিটি keyword আলাদা line-এ লিখুন",
        placeholder="best gaming headset under $30\nbest wireless earbuds 2025\nbest smartwatch for kids",
        height=180
    )
    if st.button("Bulk Add", use_container_width=True):
        if SUPABASE_URL and bulk_text.strip():
            import uuid as _uuid
            lines = [l.strip() for l in bulk_text.strip().splitlines() if l.strip()]
            h = {
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "return=representation"
            }
            added, skipped = 0, 0
            for kw in lines:
                payload = {"id": str(_uuid.uuid4()), "keyword": kw, "status": "pending"}
                r = requests.post(f"{SUPABASE_URL}/rest/v1/keyword_pool", headers=h, json=payload)
                if r.status_code in [200, 201]:
                    added += 1
                else:
                    skipped += 1
            st.success(f"Done! Added: **{added}**, Skipped (duplicate): **{skipped}**")

# ── RIGHT: View & Delete Keywords ──
with kw_col2:
    st.markdown("##### 📊 Current Keyword Pool")

    if st.button("🔄 Load Keywords", use_container_width=True):
        if SUPABASE_URL:
            h = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
            r = requests.get(
                f"{SUPABASE_URL}/rest/v1/keyword_pool?select=id,keyword,status,createdAt&order=createdAt.desc&limit=100",
                headers=h
            )
            if r.status_code == 200 and r.json():
                kw_data = r.json()
                st.session_state["kw_pool"] = kw_data

                # Stats
                total   = len(kw_data)
                pending = sum(1 for k in kw_data if k.get("status") == "pending")
                done    = sum(1 for k in kw_data if k.get("status") == "processed")
                failed  = sum(1 for k in kw_data if k.get("status") == "failed")

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Total", total)
                m2.metric("Pending", pending, delta=f"+{pending}")
                m3.metric("Done", done)
                m4.metric("Failed", failed)

            else:
                st.info("Keyword pool is empty.")
                st.session_state["kw_pool"] = []

    # Display table if loaded
    if "kw_pool" in st.session_state and st.session_state["kw_pool"]:
        df = pd.DataFrame(st.session_state["kw_pool"])
        df = df[["keyword", "status", "createdAt"]].rename(columns={
            "keyword": "Keyword", "status": "Status", "createdAt": "Added"
        })

        # Color-code status
        def color_status(val):
            colors = {"pending": "background-color:#1a3a1a; color:#4ade80",
                      "processed": "background-color:#1a1a3a; color:#60a5fa",
                      "failed": "background-color:#3a1a1a; color:#f87171"}
            return colors.get(val, "")

        st.dataframe(
            df.style.applymap(color_status, subset=["Status"]),
            use_container_width=True, height=300
        )

        st.markdown("---")
        st.markdown("##### 🗑 Keyword Delete করুন")
        del_kw = st.selectbox(
            "Delete করার keyword বেছে নিন",
            options=[""] + [k["keyword"] for k in st.session_state["kw_pool"]]
        )
        col_del1, col_del2 = st.columns(2)
        with col_del1:
            if st.button("Delete Selected", use_container_width=True):
                if del_kw and SUPABASE_URL:
                    h = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
                    from urllib.parse import quote
                    r = requests.delete(
                        f"{SUPABASE_URL}/rest/v1/keyword_pool?keyword=eq.{quote(del_kw)}",
                        headers=h
                    )
                    if r.status_code in [200, 204]:
                        st.success(f"Deleted: **{del_kw}**")
                        st.session_state.pop("kw_pool", None)
                        st.rerun()
                    else:
                        st.error(f"Error: {r.text[:100]}")
        with col_del2:
            if st.button("Delete All FAILED", use_container_width=True):
                if SUPABASE_URL:
                    h = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
                    r = requests.delete(
                        f"{SUPABASE_URL}/rest/v1/keyword_pool?status=eq.failed",
                        headers=h
                    )
                    if r.status_code in [200, 204]:
                        st.success("All failed keywords deleted.")
                        st.session_state.pop("kw_pool", None)
                        st.rerun()
