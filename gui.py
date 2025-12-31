import streamlit as st
import pandas as pd
import os
import time
import base64
import requests
from main import main as run_bot
from config import NICHE_KEYWORDS, WP_URL, SCRAPINGANT_API_KEYS, GEMINI_API_KEYS, N8N_WEBHOOK_URL, WP_USERNAME, WP_APP_PASSWORD, SUPABASE_URL, SUPABASE_KEY, AUTO_KEY

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
        data = {
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
st.set_page_config(
    page_title="Amazon Affili-Bot Cloud",
    page_icon="☁️",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
        st.stop()

# Custom CSS for Modern Glassmorphism Look (Preserved)
st.markdown("""
<style>
    /* Global Text Color */
    .stApp, .stText, .stMarkdown, h1, h2, h3 {
        color: #ffffff !important;
        font-family: 'Segoe UI', sans-serif;
    }

    /* Glassmorphism Sidebar */
    section[data-testid="stSidebar"] {
        background: rgba(0, 0, 0, 0.4);
        backdrop-filter: blur(15px);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Buttons */
    .stButton>button {
        width: 100%;
        background: linear-gradient(90deg, #FF9900 0%, #FFB84D 100%);
        color: black !important;
        border: none;
        border-radius: 8px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(255, 153, 0, 0.4);
    }

    /* Inputs */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea, .stNumberInput>div>div>input {
        background-color: rgba(255, 255, 255, 0.1) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
    }
    
    /* Success/Error Text */
    .success-text { color: #00ff88; }
    .error-text { color: #ff4d4d; }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
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
# 🧠 SIDEBAR & CONFIG
# ==========================================
sites = load_sites()

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/4712/4712035.png", width=50)
    st.title("Admin Console (Cloud)")
    
    if not SUPABASE_URL:
        st.error("⚠️ Connect to Supabase first!")
    
    # --- SITE MANAGER ---
    with st.expander("🌍 Site Manager", expanded=True):
        
        # Add New Site
        with st.form("add_site_form"):
            st.caption("Add New WordPress Site")
            new_name = st.text_input("Name")
            new_url = st.text_input("WP URL")
            new_user = st.text_input("Username")
            new_pass = st.text_input("App Password", type="password")
            new_n8n = st.text_input("n8n Webhook (Optional)")
            
            if st.form_submit_button("Add Site"):
                if new_name and new_url:
                    if add_site(new_name, new_url, new_user, new_pass, new_n8n):
                        st.success("Site Added!")
                        st.rerun()

        # Delete Sites
        st.divider()
        st.caption("Existing Sites:")
        for site in sites:
            c1, c2 = st.columns([3, 1])
            c1.text(f"🔹 {site['name']}")
            # Don't allow delete if only 1 site? Nah, user can maximize freedom.
            if c2.button("🗑️", key=f"del_{site['id']}"):
                if delete_site(site['id']):
                    st.rerun()

    st.divider()

    # --- SETTINGS ---
    st.subheader("⚙️ Global Settings")
    max_keywords = st.number_input("Keywords Limit", 1, 50, 1)
    products_per_keyword = st.number_input("Products/Keyword", 1, 10, 3)
    max_total_articles = st.number_input("Total Max Articles", 0, 100, 5)
    
    st.caption("Content Features")
    use_comparison = st.toggle("Comparison Table", False)
    use_internal_links = st.toggle("Internal Links", True)
    publish_wp = st.toggle("Publish to WP", True)
    trigger_n8n = st.toggle("n8n Auto-Post", True, disabled=not publish_wp)

    st.caption("Delays (sec)")
    delay_products = st.slider("Product Delay", 0, 60, 3)
    delay_keywords = st.slider("Keyword Delay", 0, 120, 5)

# ==========================================
# 🚀 MAIN DASHBOARD
# ==========================================
st.markdown("<h1 style='text-align: center; margin-bottom: 30px;'>🚀 Affiliate Cloud Command</h1>", unsafe_allow_html=True)

if not sites:
    st.warning("⚠️ No sites configured. Please add a site in the sidebar.")
    st.stop()

# Select Target Site
site_names = [s['name'] for s in sites]
selected_site_idx = 0
if 'last_selected_site' in st.session_state:
    if st.session_state.last_selected_site in site_names:
        selected_site_idx = site_names.index(st.session_state.last_selected_site)

selected_site_name = st.selectbox("📣 Select Target Website:", site_names, index=selected_site_idx)
st.session_state.last_selected_site = selected_site_name

# Find the full site object
selected_site = next((s for s in sites if s['name'] == selected_site_name), sites[0])

tab1, tab2, tab3, tab4 = st.tabs(["📊 Live Monitor", "📝 Keywords", "💾 Cloud DB", "🔧 Tools"])

# --- TAB 1: LIVE MONITOR ---
with tab1:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📜 System Logs")
        log_container = st.container()
        log_area = log_container.empty()
        logs = []

        def log_to_gui(message):
            timestamp = time.strftime("%H:%M:%S")
            formatted_msg = f"[{timestamp}] {message}"
            logs.append(formatted_msg)
            if len(logs) > 100: logs.pop(0)
            log_area.code("\n".join(logs), language="text")

    with col2:
        st.markdown("### 🎮 Controls")
        st.info(f"Target: **{selected_site['name']}**\nKeywords: {len(selected_site.get('keywords', []) or [])}")
        
        if st.button("🚀 IGNITE AUTOMATION", type="primary"):
            config = {
                'max_keywords': max_keywords,
                'products_per_keyword': products_per_keyword,
                'max_total_articles': max_total_articles,
                'use_comparison': use_comparison,
                'use_internal_links': use_internal_links,
                'publish_wp': publish_wp,
                'trigger_n8n': trigger_n8n,
                'delay_between_products': delay_products,
                'delay_between_keywords': delay_keywords
            }
            
            with st.status("🤖 Bot is running on Cloud Data...", expanded=True) as status:
                try:
                    stats = run_bot(config=config, log_function=log_to_gui, site_config=selected_site)
                    status.update(label="✅ Mission Complete!", state="complete")
                    
                    st.success(f"Summary: {stats['articles_published']} Published, {stats['errors']} Errors")
                    if stats['articles_published'] > 0: st.balloons()    
                except Exception as e:
                    status.update(label="❌ Failed", state="error")
                    st.error(f"Error: {e}")
                    log_to_gui(f"CRITICAL: {e}")

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
