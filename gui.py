import streamlit as st
import pandas as pd
import os
import time
import threading
from main import main as run_bot
from config import NICHE_KEYWORDS, WP_URL, SCRAPINGANT_API_KEYS, GEMINI_API_KEYS

# Page Config
st.set_page_config(
    page_title="Amazon Affiliate Bot",
    page_icon="🤖",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
        background-color: #FF9900;
        color: white;
        border: none;
        border-radius: 5px;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #e68a00;
        color: white;
    }
    .success-text { color: #28a745; }
    .error-text { color: #dc3545; }
</style>
""", unsafe_allow_html=True)

# Title
st.title("🤖 Amazon Affiliate Automation Bot")
st.markdown("Automate your niche site content generation with AI.")

# Sidebar - Configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Credentials Status
    st.subheader("APIs & Credentials")
    if SCRAPINGANT_API_KEYS:
        st.caption(f"✅ ScrapingAnt Keys: {len(SCRAPINGANT_API_KEYS)} loaded")
    else:
        st.caption("❌ ScrapingAnt Keys: Missing")
        
    if GEMINI_API_KEYS:
        st.caption(f"✅ Gemini Keys: {len(GEMINI_API_KEYS)} loaded")
    else:
        st.caption("❌ Gemini Keys: Missing")
        
    st.caption(f"🌍 WordPress: {WP_URL}")

    st.divider()

    # Processing Limits
    st.subheader("Processing Limits")
    max_keywords = st.number_input("Keywords to Process", min_value=1, max_value=50, value=1)
    products_per_keyword = st.number_input("Products per Keyword", min_value=1, max_value=10, value=2)
    max_total_articles = st.number_input("Max Articles (0=Unlimited)", min_value=0, max_value=100, value=5)

    st.divider()

    # Features
    st.subheader("Features")
    use_comparison = st.checkbox("Include Comparison Table", value=False, help="Uses more API credits")
    use_internal_links = st.checkbox("Include Internal Links", value=True)
    publish_wp = st.checkbox("Publish to WordPress", value=True)
    trigger_n8n = st.checkbox("Trigger n8n Automation (Facebook Auto-Post)", value=True, disabled=not publish_wp)

    st.divider()

    # Delays
    st.subheader("Delays (Seconds)")
    delay_products = st.slider("Between Products", 0, 60, 3)
    delay_keywords = st.slider("Between Keywords", 0, 120, 5)

# Main Content Area
tab1, tab2, tab3, tab4 = st.tabs(["🚀 Dashboard", "📝 Keyword Manager", "📊 Database", "🧪 n8n Tester"])

with tab4:
    st.header("🧪 n8n Webhook Tester")
    st.info("Use this tool to manually send data to your n8n workflow and verify if it's working.")
    
    with st.form("n8n_test_form"):
        col1, col2 = st.columns(2)
        with col1:
            test_title = st.text_input("Product Title", "Test Product: Retro Console")
            test_category = st.text_input("Category", "Gaming")
            test_price = st.text_input("Price", "$99.99")
        with col2:
            test_url = st.text_input("Amazon Link", "https://amazon.com/dp/B00EXAMPLE")
            test_image = st.text_input("Image URL", "https://via.placeholder.com/600")
            
        test_desc = st.text_area("Description", "This is a test description sent from the Amazon Affiliate Bot GUI to verify n8n integration.")
        
        submitted = st.form_submit_button("📡 Send Test Data to n8n")
        
        if submitted:
            from n8n_handler import trigger_n8n_workflow
            from config import N8N_WEBHOOK_URL
            
            st.write(f"Target URL: `{N8N_WEBHOOK_URL}`")
            
            with st.spinner("Sending webhook..."):
                # We mock the long description as HTML for the test
                dummy_html = f"<h1>{test_title}</h1><p>{test_desc}</p>"
                
                success = trigger_n8n_workflow(
                    title=test_title,
                    amazon_link=test_url,
                    image_url=test_image,
                    social_caption=f"Check out {test_title}!",
                    category=test_category,
                    long_description=dummy_html
                )
                
                if success:
                    st.success("✅ Webhook sent successfully! Check your n8n Executions tab.")
                else:
                    st.error("❌ Failed to send webhook. Check logs and connection.")

with tab1:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Live Logs")
        log_container = st.container()
        log_area = log_container.empty()
        logs = []

        def log_to_gui(message):
            """Callback function to update GUI logs"""
            # Add timestamp
            timestamp = time.strftime("%H:%M:%S")
            formatted_msg = f"[{timestamp}] {message}"
            logs.append(formatted_msg)
            # Keep only last 100 logs
            if len(logs) > 100:
                logs.pop(0)
            
            # Update the log area
            log_text = "\n".join(logs)
            log_area.code(log_text, language="text")

    with col2:
        st.subheader("Actions")
        if st.button("🚀 Start Automation", type="primary"):
            # Construct Config Dictionary
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
            
            with st.spinner("Bot is running... checks logs for details"):
                try:
                    stats = run_bot(config=config, log_function=log_to_gui)
                    st.success("Session Completed!")
                    
                    # Show Stats
                    st.metric("Products Processed", stats['total_processed'])
                    st.metric("Articles Generated", stats['articles_generated'])
                    st.metric("Articles Published", stats['articles_published'])
                    st.metric("Errors", stats['errors'])
                    
                except Exception as e:
                    st.error(f"An error occurred: {e}")
                    log_to_gui(f"ERROR: {e}")

with tab2:
    st.subheader("Manage Keywords")
    
    # Read Keywords
    try:
        if os.path.exists("keywords.txt"):
            with open("keywords.txt", "r") as f:
                current_keywords = f.read()
        else:
            current_keywords = ""
    except Exception as e:
        st.error(f"Error reading keywords: {e}")
        current_keywords = ""

    # Editor
    new_keywords = st.text_area("Keywords (One per line)", value=current_keywords, height=300)
    
    if st.button("💾 Save Keywords"):
        try:
            with open("keywords.txt", "w") as f:
                f.write(new_keywords)
            st.success("Keywords saved successfully!")
        except Exception as e:
            st.error(f"Error saving keywords: {e}")

    # Show Processed
    with st.expander("View Processed Keywords"):
        try:
            if os.path.exists("processed_keywords.txt"):
                with open("processed_keywords.txt", "r") as f:
                    st.text(f.read())
            else:
                st.info("No keywords processed yet.")
        except:
            pass

with tab3:
    st.subheader("Product Database")
    if st.button("Refresh Data"):
        import sqlite3
        try:
            conn = sqlite3.connect("amazon_products.db")
            df = pd.read_sql_query("SELECT * FROM products ORDER BY created_at DESC", conn)
            conn.close()
            st.dataframe(df)
        except Exception as e:
            st.error(f"Could not load database: {e}")
    else:
        st.info("Click Refresh to load data from SQLite database.")
