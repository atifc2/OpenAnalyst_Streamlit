from utils.data_handler import read_and_clean_files, get_clean_csv_download, create_data_profile
from utils.ai_core import get_ai_response
from utils.ui_components import render_chat_response, render_canvas_item
from utils.auth import render_login, check_authentication, initialize_authenticator
from utils.onboarding import render_onboarding_modal, should_show_onboarding, add_sample_datasets_section
import streamlit as st
import pandas as pd
import datetime
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set the page configuration for a wide layout and a professional title.
st.set_page_config(layout="wide", page_title="OpenAnalyst - AI Data Analysis", initial_sidebar_state="expanded")

# ==================== ADAPTIVE THEME: WORKS IN DARK & LIGHT MODE ====================
# Professional theme with Netflix red accent that adapts to system preference
st.markdown("""
<style>
    /* ==================== NETFLIX COLOR PALETTE ==================== */
    :root {
        --netflix-red: #E50914;
        --netflix-red-dark: #B20710;
        --netflix-red-light: #F40612;
        --netflix-black: #141414;
        --netflix-dark: #1F1F1F;
        --netflix-gray: #2F2F2F;
        --netflix-light-gray: #808080;
        --netflix-white: #FFFFFF;
        --netflix-text: #E5E5E5;
    }
    
    /* ==================== MAIN CONTENT ==================== */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* ==================== BUTTONS - Always Netflix Red ==================== */
    .stButton > button {
        background: linear-gradient(135deg, #E50914 0%, #B20710 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 4px !important;
        font-weight: 600 !important;
        padding: 0.5rem 1rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 2px 8px rgba(229, 9, 20, 0.3) !important;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #F40612 0%, #E50914 100%) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 16px rgba(229, 9, 20, 0.4) !important;
    }
    
    /* Secondary buttons */
    .stButton > button[kind="secondary"] {
        background: transparent !important;
        border: 2px solid #E50914 !important;
        color: #E50914 !important;
        box-shadow: none !important;
    }
    
    .stButton > button[kind="secondary"]:hover {
        background: rgba(229, 9, 20, 0.1) !important;
    }
    
    /* ==================== INPUTS - Red focus accent ==================== */
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #E50914 !important;
        box-shadow: 0 0 0 2px rgba(229, 9, 20, 0.2) !important;
    }
    
    /* Chat input focus */
    .stChatInput > div:focus-within {
        border-color: #E50914 !important;
        box-shadow: 0 0 0 2px rgba(229, 9, 20, 0.2) !important;
    }
    
    /* ==================== TABS - Netflix Red Active State ==================== */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0 !important;
        padding: 10px 20px !important;
        font-weight: 500 !important;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #E50914 !important;
        color: white !important;
    }
    
    /* ==================== FILE UPLOADER - Theme Adaptive with Red Hover ==================== */
    [data-testid="stFileUploader"] {
        border: 2px dashed #666 !important;
        border-radius: 12px !important;
        padding: 2rem !important;
        transition: all 0.3s ease !important;
    }
    
    [data-testid="stFileUploader"]:hover {
        border-color: #E50914 !important;
        background-color: rgba(229, 9, 20, 0.05) !important;
    }
    
    /* File uploader inner content - FORCE VISIBILITY */
    [data-testid="stFileUploader"] section {
        background: transparent !important;
    }
    
    [data-testid="stFileUploader"] section > div {
        padding: 1rem !important;
    }
    
    [data-testid="stFileUploader"] button {
        background: linear-gradient(135deg, #E50914 0%, #B20710 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 4px !important;
    }
    
    /* ==================== PROGRESS BAR ==================== */
    .stProgress > div > div {
        background: linear-gradient(90deg, #E50914 0%, #F40612 100%) !important;
        border-radius: 10px !important;
    }
    
    /* ==================== ALERTS & MESSAGES ==================== */
    .stAlert {
        border-radius: 8px !important;
    }
    
    [data-testid="stAlertSuccess"] {
        border-left: 4px solid #22C55E !important;
    }
    
    [data-testid="stAlertWarning"] {
        border-left: 4px solid #F59E0B !important;
    }
    
    [data-testid="stAlertError"] {
        border-left: 4px solid #E50914 !important;
    }
    
    [data-testid="stAlertInfo"] {
        border-left: 4px solid #3B82F6 !important;
    }
    
    /* ==================== METRIC CARDS - Red Accent ==================== */
    [data-testid="stMetric"] {
        padding: 1rem !important;
        border-radius: 8px !important;
        border-left: 4px solid #E50914 !important;
    }
    
    /* ==================== CHAT MESSAGES ==================== */
    [data-testid="stChatMessage"] {
        border-radius: 12px !important;
        padding: 1rem !important;
        margin-bottom: 0.5rem !important;
    }
    
    /* ==================== ANIMATIONS ==================== */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .main .block-container > div {
        animation: fadeIn 0.4s ease-out;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    
    .loading-pulse {
        animation: pulse 1.5s ease-in-out infinite;
    }
    
    @keyframes shimmer {
        0% { background-position: -200% 0; }
        100% { background-position: 200% 0; }
    }
    
    .loading-shimmer {
        background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
        background-size: 200% 100%;
        animation: shimmer 1.5s infinite;
    }
    
    /* ==================== SCROLLBAR ==================== */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #666;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #E50914;
    }
    
    /* ==================== CUSTOM COMPONENTS ==================== */
    .oa-card {
        padding: 20px;
        border-radius: 12px;
        border: 1px solid rgba(128, 128, 128, 0.3);
        margin-bottom: 15px;
        transition: all 0.3s ease;
    }
    
    .oa-card:hover {
        border-color: #E50914;
        box-shadow: 0 4px 20px rgba(229, 9, 20, 0.15);
    }
    
    .oa-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
    }
    
    .oa-badge-red {
        background: rgba(229, 9, 20, 0.15);
        color: #E50914;
        border: 1px solid rgba(229, 9, 20, 0.3);
    }
    
    .oa-badge-green {
        background: rgba(34, 197, 94, 0.15);
        color: #22C55E;
        border: 1px solid rgba(34, 197, 94, 0.3);
    }
    
    /* ==================== LOADING STATES ==================== */
    .loading-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 40px;
        text-align: center;
    }
    
    .loading-spinner {
        width: 50px;
        height: 50px;
        border: 4px solid rgba(229, 9, 20, 0.2);
        border-top-color: #E50914;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
</style>
""", unsafe_allow_html=True)

# --- Authentication Check ---
if not check_authentication():
    # Compact Landing Page - Login Above the Fold
    st.markdown("""
    <div style='
        padding: 15px 20px;
        margin: -1rem -1rem 1rem -1rem;
        border-bottom: 2px solid #E50914;
        text-align: center;
    '>
        <h1 style='
            color: #E50914;
            font-size: 36px;
            font-weight: 900;
            margin: 0 0 5px 0;
            letter-spacing: -1px;
            font-family: Arial Black, sans-serif;
        '>OPENANALYST</h1>
        <p style='font-size: 14px; margin: 0; opacity: 0.85;'>
            AI-Powered Data Analysis with <span style="color: #E50914; font-weight: 700;">Advanced RAG</span> • 
            200+ templates • 8 domains
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Two-column layout: Login OR Try Demo - IMMEDIATELY visible
    col_left, col_right = st.columns([1, 1], gap="large")
    
    with col_left:
        st.markdown("#### 🔐 Login")
        render_login()
    
    with col_right:
        st.markdown("#### 🚀 Try Demo")
        
        # Compact sample data buttons
        sample_datasets = [
            ("🛒 E-commerce Sales", "Sample_Datasets/sample_ecommerce_sales.csv"),
            ("📊 Customer Survey", "Sample_Datasets/sample_customer_survey.csv"),
            ("💰 Financial Metrics", "Sample_Datasets/sample_financial_metrics.csv")
        ]
        
        for icon_name, filename in sample_datasets:
            if st.button(f"{icon_name}", key=filename, use_container_width=True):
                with st.spinner(f"Loading {icon_name}..."):
                    st.session_state['authenticated'] = True
                    st.session_state['username'] = 'demo_user'
                    st.session_state['name'] = 'Demo User'
                    st.session_state['authentication_status'] = True
                    st.session_state.demo_sample = filename
                    st.session_state.demo_sample_name = icon_name
                    st.session_state.loading_sample = True
                st.rerun()
    
    # Feature highlights - inline compact
    st.markdown("---")
    st.markdown("""
    <div style='display: flex; justify-content: center; gap: 40px; padding: 15px 0; flex-wrap: wrap;'>
        <span>🧠 <strong>Advanced RAG</strong></span>
        <span>⚡ <strong>Instant Insights</strong></span>
        <span>🎯 <strong>8 Expert Modes</strong></span>
        <span>📚 <strong>200+ Templates</strong></span>
    </div>
    """, unsafe_allow_html=True)
    
    # How it works - more compact
    st.markdown("""
    <div style='text-align: center; padding: 10px 20px; opacity: 0.8;'>
        <span style='font-size: 13px;'>
            📁 Upload Data → 💬 Ask Questions → 🧠 AI Learns → 📊 Get Insights
        </span>
    </div>
    """, unsafe_allow_html=True)
    
    # Footer
    st.markdown("""
    <div style='text-align: center; padding: 10px; opacity: 0.6; font-size: 12px;'>
        Powered by Google Gemini AI • Qdrant Vector DB • 🔒 Your data never leaves your machine
    </div>
    """, unsafe_allow_html=True)
    
    st.stop()

# User is authenticated, show logout button
authenticator, config = initialize_authenticator()
with st.sidebar:
    st.write(f"👤 **{st.session_state.get('name', 'User')}**")
    
    # Custom logout button with proper session clearing
    if st.button("🚪 Logout", use_container_width=True, type="secondary"):
        # Clear ALL session state to ensure clean logout
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        # Force re-authentication check
        st.session_state['authenticated'] = False
        st.session_state['authentication_status'] = None
        st.rerun()

# Initialize vector DB and index sample datasets (only once per session)
if 'vector_db_initialized' not in st.session_state:
    st.session_state.vector_db_initialized = False
    st.session_state.vector_db_seeded = True  # Skip seeding by default - do it lazily

# --- Load Demo Sample if Selected ---
if 'demo_sample' in st.session_state and st.session_state.demo_sample:
    from utils.data_handler import clean_df, create_derived_columns
    import pandas as pd
    
    # Show loading indicator
    with st.spinner(f"🔄 Loading {st.session_state.demo_sample_name}... This will only take a moment!"):
        try:
            filename = st.session_state.demo_sample
            name = st.session_state.demo_sample_name
            
            # Load and process sample data
            raw_df = pd.read_csv(filename)
            original_columns = set(raw_df.columns)
            cleaned_df, junk_log = clean_df(raw_df.copy())
            cleaned_df = create_derived_columns(cleaned_df)
            derived_columns = list(set(cleaned_df.columns) - original_columns)
            
            # Initialize session state
            if 'processed_data' not in st.session_state or st.session_state.processed_data is None:
                st.session_state.processed_data = {}
            
            st.session_state.processed_data[name] = {
                'df': cleaned_df,
                'raw_df': raw_df,
                'junk_log': junk_log,
                'derived_columns': derived_columns,
                'profile': None
            }
            st.session_state.active_dataset_key = name
            st.session_state.messages = []
            
            # Clear demo sample flags
            del st.session_state.demo_sample
            del st.session_state.demo_sample_name
            if 'loading_sample' in st.session_state:
                del st.session_state.loading_sample
            
            st.success(f"✅ {name} loaded successfully!")
            time.sleep(0.5)  # Brief pause to show success message
            st.rerun()
        except Exception as e:
            st.error(f"❌ Failed to load sample data: {str(e)}")
            if 'demo_sample' in st.session_state:
                del st.session_state.demo_sample
            if 'demo_sample_name' in st.session_state:
                del st.session_state.demo_sample_name
            if 'loading_sample' in st.session_state:
                del st.session_state.loading_sample
            st.stop()

# --- Show Onboarding for First-Time Users ---
if should_show_onboarding():
    render_onboarding_modal()
    st.stop()

# --- Debug Mode Toggle (Hidden - only accessible via URL parameter) ---
# Access with: http://localhost:8501/?debug=true
ADMIN_MODE = st.query_params.get("admin", "false").lower() == "true"

if ADMIN_MODE:
    with st.sidebar:
        st.write("🔧 Admin Mode Active")
        
DEBUG_MODE = st.query_params.get("debug", "false").lower() == "true"

def debug_log(message):
    """Only shows debug messages if debug mode is enabled"""
    if DEBUG_MODE:
        st.sidebar.info(f"🔍 Debug: {message}")

# --- Initialize Session State ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "processed_data" not in st.session_state:
    st.session_state.processed_data = None
if "active_dataset_key" not in st.session_state:
    st.session_state.active_dataset_key = None
if "canvas_items" not in st.session_state:
    st.session_state.canvas_items = []
if "report_mode" not in st.session_state:
    st.session_state.report_mode = False
if "last_uploaded_files" not in st.session_state:
    st.session_state.last_uploaded_files = None

# --- 1. Data Context Panel (Sidebar) ---
with st.sidebar:
    # Netflix-style sidebar header
    st.markdown("""
    <div style='
        text-align: center;
        padding: 15px 0;
        margin-bottom: 15px;
        border-bottom: 2px solid #E50914;
    '>
        <h2 style='
            color: #E50914;
            font-weight: 900;
            font-size: 24px;
            margin: 0;
            letter-spacing: -1px;
        '>OPENANALYST</h2>
        <p style='color: #808080; font-size: 11px; margin: 5px 0 0 0;'>Advanced RAG • AI Analysis</p>
    </div>
    """, unsafe_allow_html=True)
    
    # ==================== 🏢 HYBRID TIER INDICATOR ====================
    current_user = st.session_state.get('username', 'Guest')
    user_tier = "free"  # Default tier (later: check from database)
    
    tier_config = {
        "free": {
            "badge": "🆓 FREE",
            "color": "#E50914",
            "workspace": "Personal Workspace",
            "description": "200+ community templates + your private analyses"
        },
        "pro": {
            "badge": "⭐ PRO",
            "color": "#F59E0B",
            "workspace": "Pro Workspace",
            "description": "Unlimited analyses + priority support"
        },
        "team": {
            "badge": "👥 TEAM",
            "color": "#8B5CF6",
            "workspace": "Team Workspace",
            "description": "Share with your team + collaboration features"
        }
    }
    
    tier_info = tier_config.get(user_tier, tier_config["free"])
    
    st.markdown(
        f"""
        <div style='
            padding: 12px;
            border-radius: 8px;
            background: linear-gradient(145deg, #1a1a1a, #252525);
            border-left: 4px solid {tier_info['color']};
            margin-bottom: 15px;
        '>
            <div style='font-weight: 700; color: {tier_info['color']}; margin-bottom: 5px;'>
                {tier_info['badge']} • {tier_info['workspace']}
            </div>
            <div style='font-size: 0.85em; color: #B3B3B3;'>
                👤 {current_user}<br/>
                {tier_info['description']}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Model Selector
    st.divider()
    st.subheader("🤖 AI Model")
    
    # Available models with status - categorized
    model_options = {
        # ===== ACTIVE MODELS (API Connected) =====
        "gemini-2.5-flash": "✅ Gemini Flash (Fast)",
        "gemini-2.5-flash-lite": "✅ Gemini Flash Lite (Free)",
        "gemini-2.5-flash-8b": "✅ Gemini Flash-8B (Efficient)",
        
        # ===== PREMIUM MODELS (Coming Soon) =====
        "gemini-2.0-pro": "⭐ Gemini 2.0 Pro (Coming Soon)",
        "gpt-4o": "🔒 GPT-4o (Add API Key)",
        "gpt-4o-mini": "🔒 GPT-4o Mini (Add API Key)",
        "claude-3.5-sonnet": "🔒 Claude 3.5 Sonnet (Add API Key)",
        "claude-3-opus": "🔒 Claude 3 Opus (Add API Key)",
        
        # ===== OPEN SOURCE (Self-Host) =====
        "llama-3.2-70b": "🦙 Llama 3.2 70B (Self-Host)",
        "mistral-large": "🌀 Mistral Large (Self-Host)",
        "mixtral-8x7b": "🌀 Mixtral 8x7B (Self-Host)",
        "qwen-2.5-72b": "🔮 Qwen 2.5 72B (Self-Host)",
    }
    
    # Models that are actually available
    active_models = ["gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-2.5-flash-8b"]
    
    if "selected_model" not in st.session_state:
        st.session_state.selected_model = "gemini-2.5-flash-lite"
    
    selected_model = st.selectbox(
        "Select Model:",
        options=list(model_options.keys()),
        format_func=lambda x: model_options[x],
        index=list(model_options.keys()).index(st.session_state.selected_model),
        key="model_selector"
    )
    
    # Check if model changed
    if selected_model != st.session_state.selected_model:
        if selected_model not in active_models:
            # Show appropriate message based on model type
            if "gpt" in selected_model or "claude" in selected_model:
                st.warning("� Add your OpenAI/Anthropic API key in settings to use this model.")
            elif "llama" in selected_model or "mistral" in selected_model or "mixtral" in selected_model or "qwen" in selected_model:
                st.info("🖥️ Self-hosted models require local setup. Contact us for enterprise deployment.")
            else:
                st.info("🚀 This model is coming soon! Stay tuned.")
            # Don't change selection for unavailable models
        else:
            # Update to active model
            st.session_state.selected_model = selected_model
            from utils.ai_core import client as gemini_client
            gemini_client.set_model(selected_model)
            st.success(f"✅ Switched to {model_options[selected_model]}")
            st.rerun()
    
    st.caption(f"**Active:** {model_options[st.session_state.selected_model]}")
    
    st.divider()
    
    # Show Similar Analyses Widget (if data is loaded)
    if st.session_state.active_dataset_key and st.session_state.processed_data:
        try:
            from utils.domain_detector import detect_data_domain, get_domain_emoji
            from utils.vector_db import get_vector_store
            from utils.similar_analyses_widget import render_similar_analyses_widget
            
            # Get active dataframe
            active_df = st.session_state.processed_data[st.session_state.active_dataset_key]["df"]
            
            # AUTO-DETECT domain (but allow manual override!)
            if 'current_domain_info' not in st.session_state or st.session_state.previous_dataset_key != st.session_state.active_dataset_key:
                domain_info = detect_data_domain(active_df)
                st.session_state.current_domain_info = domain_info
                st.session_state.auto_detected_domain = domain_info['domain']  # Store auto-detected
            else:
                domain_info = st.session_state.current_domain_info
            
            # ==================== 🎯 ANALYST MODE SELECTOR ====================
            st.markdown("### 🎯 Select Analyst Mode")
            
            all_domains = ["sales", "marketing", "hr", "financial", "survey", "product", "business", "operations", "general"]
            domain_labels = {
                "sales": "🛒 Sales Analyst",
                "marketing": "📢 Marketing Analyst", 
                "hr": "👥 HR Analyst",
                "financial": "💰 Financial Analyst",
                "survey": "📋 Survey Analyst",
                "product": "📦 Product Analyst",
                "business": "💼 Business Analyst",
                "operations": "🎯 Operations Analyst",
                "general": "📊 General Analyst"
            }
            
            # Get current mode (manual override or auto-detected)
            current_mode = st.session_state.get('manual_domain_override', domain_info.get('domain', 'general'))
            auto_detected = st.session_state.get('auto_detected_domain', domain_info.get('domain', 'general'))
            
            # Ensure current_mode is in the list
            if current_mode not in all_domains:
                current_mode = 'general'
            
            # Show selector
            selected_domain = st.selectbox(
                "Choose your analyst perspective:",
                options=all_domains,
                format_func=lambda x: domain_labels.get(x, x),
                index=all_domains.index(current_mode) if current_mode in all_domains else 0,
                help=f"🤖 Auto-detected: {domain_labels.get(auto_detected, 'General Analyst')}\n\n💡 Or choose a different analyst mode to get specialized templates!"
            )
            
            # Store manual override
            if selected_domain != auto_detected:
                st.session_state.manual_domain_override = selected_domain
                st.info(f"✨ Switched to {domain_labels[selected_domain]} mode (overriding auto-detection)")
            else:
                st.session_state.manual_domain_override = None
            
            # Use selected domain (not auto-detected)
            domain_info['domain'] = selected_domain
            st.session_state.current_domain_info = domain_info
            
            st.divider()
            
            # Vector DB is seeded at startup only - no need to seed here
            # This makes data loading much faster!
            
            # Render similar analyses widget (HYBRID MODEL!)
            vector_store = get_vector_store()
            current_user_id = st.session_state.get('username', 'anonymous')  # Get from auth
            render_similar_analyses_widget(
                vector_store=vector_store,
                current_domain=domain_info['domain'],
                current_dataset_name=st.session_state.active_dataset_key,
                user_id=current_user_id
            )
            
        except Exception as e:
            import traceback
            logger.error(f"Error rendering similar analyses: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            st.error(f"⚠️ Widget error: {str(e)}")
            st.divider()
    
    uploaded_files = st.file_uploader(
        "Upload Files", type=["csv", "xlsx"], accept_multiple_files=True,
        help="Drop your CSV or Excel files here to start analysis"
    )
    
    # Only process if files have changed
    if uploaded_files:
        current_file_names = tuple(f.name for f in uploaded_files)
        
        if current_file_names != st.session_state.last_uploaded_files:
            debug_log("🔍 New files detected, processing...")
            
            # Show loading state with progress
            loading_placeholder = st.empty()
            with loading_placeholder.container():
                st.markdown("""
                <div style='
                    text-align: center;
                    padding: 20px;
                    border-radius: 8px;
                    border: 1px solid rgba(229, 9, 20, 0.3);
                    background: rgba(229, 9, 20, 0.05);
                '>
                    <div style='font-size: 24px; margin-bottom: 10px;'>🔄</div>
                    <div style='font-weight: 600; color: #E50914;'>Processing Your Data...</div>
                    <div style='font-size: 12px; color: #808080; margin-top: 5px;'>Cleaning, validating, and preparing for analysis</div>
                </div>
                """, unsafe_allow_html=True)
                
            try:
                # Archive current chat before clearing (if it has messages)
                if st.session_state.messages and st.session_state.active_dataset_key:
                    if "chat_archives" not in st.session_state:
                        st.session_state.chat_archives = []
                    
                    archive = {
                        "dataset": st.session_state.active_dataset_key,
                        "messages": st.session_state.messages.copy(),
                        "archived_at": datetime.datetime.now().strftime("%H:%M:%S"),
                        "message_count": len(st.session_state.messages)
                    }
                    st.session_state.chat_archives.append(archive)
                
                st.session_state.messages = []
                # DON'T clear canvas_items - this keeps them persistent
                st.session_state.processed_data = read_and_clean_files(tuple(uploaded_files))
                st.session_state.last_uploaded_files = current_file_names
                debug_log(f"✅ Processed {len(st.session_state.processed_data)} datasets")
                
                # Clear loading and show success
                loading_placeholder.empty()
                st.success(f"✅ Successfully loaded {len(st.session_state.processed_data)} dataset(s)!")
                time.sleep(0.5)
                st.rerun()
            except Exception as e:
                loading_placeholder.empty()
                st.error(f"Failed to process files: {e}")
    
    if st.session_state.processed_data:
        dataset_keys = list(st.session_state.processed_data.keys())
        
        # Track previous dataset to detect changes
        if "previous_dataset_key" not in st.session_state:
            st.session_state.previous_dataset_key = st.session_state.active_dataset_key
        
        # Group datasets by file (for multi-tab Excel files)
        files_dict = {}
        for key in dataset_keys:
            if '|' in key:
                filename, sheetname = key.rsplit('|', 1)
            else:
                filename, sheetname = key, 'Sheet1'
            
            if filename not in files_dict:
                files_dict[filename] = []
            files_dict[filename].append((key, sheetname))
        
        # Smart selector: Use dropdown when many datasets, radio for few
        if len(dataset_keys) > 5:
            # Multi-tab Excel detected! Use hierarchical dropdown
            st.markdown("### 📁 Select Dataset")
            
            # File selector
            file_names = list(files_dict.keys())
            current_key = st.session_state.active_dataset_key or dataset_keys[0]
            current_file = current_key.rsplit('|', 1)[0] if '|' in current_key else current_key
            
            selected_file = st.selectbox(
                "📄 File:",
                options=file_names,
                index=file_names.index(current_file) if current_file in file_names else 0,
                key="file_selector"
            )
            
            # Sheet selector (only show if multiple sheets in selected file)
            sheets = files_dict[selected_file]
            if len(sheets) > 1:
                sheet_options = [s[0] for s in sheets]  # Full keys
                sheet_labels = [s[1] for s in sheets]   # Sheet names only
                
                current_sheet_idx = 0
                if current_key in sheet_options:
                    current_sheet_idx = sheet_options.index(current_key)
                
                selected_dataset = st.selectbox(
                    "📊 Sheet:",
                    options=sheet_options,
                    format_func=lambda x: x.rsplit('|', 1)[1] if '|' in x else 'Sheet1',
                    index=current_sheet_idx,
                    key="sheet_selector"
                )
                
                # Show sheet count info
                st.caption(f"📋 {len(sheets)} sheets in this file")
            else:
                selected_dataset = sheets[0][0]
        else:
            # Simple case: radio buttons for few datasets
            selected_dataset = st.radio("📁 Select Dataset:", dataset_keys, 
                                        index=dataset_keys.index(st.session_state.active_dataset_key) if st.session_state.active_dataset_key in dataset_keys else 0)
        
        # Detect dataset change
        if selected_dataset != st.session_state.active_dataset_key and st.session_state.messages:
            st.warning("⚠️ **Switching datasets will archive your chat history** (Canvas is preserved)")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Switch & Archive Chat", type="primary", use_container_width=True):
                    # Archive current chat before switching
                    if st.session_state.messages:
                        if "chat_archives" not in st.session_state:
                            st.session_state.chat_archives = []
                        
                        archive = {
                            "dataset": st.session_state.active_dataset_key,
                            "messages": st.session_state.messages.copy(),
                            "archived_at": datetime.datetime.now().strftime("%H:%M:%S"),
                            "message_count": len(st.session_state.messages)
                        }
                        st.session_state.chat_archives.append(archive)
                    
                    # Show switching loading state
                    with st.spinner("🔄 Switching to new dataset..."):
                        st.session_state.active_dataset_key = selected_dataset
                        st.session_state.messages = []
                        st.session_state.previous_dataset_key = selected_dataset
                        time.sleep(0.3)  # Brief visual feedback
                    st.toast(f"📦 Chat archived! Switched to {selected_dataset}", icon="✅")
                    st.rerun()
            with col2:
                if st.button("❌ Cancel", use_container_width=True):
                    # Keep current dataset
                    st.rerun()
        elif selected_dataset != st.session_state.active_dataset_key:
            # No chat history, switch immediately with loading state
            with st.spinner("🔄 Loading dataset..."):
                st.session_state.active_dataset_key = selected_dataset
                st.session_state.previous_dataset_key = selected_dataset
                time.sleep(0.2)  # Brief visual feedback
            st.rerun()
        
        active_df = st.session_state.processed_data[st.session_state.active_dataset_key]["df"]
        
        # Visual indicator for active dataset
        st.success(f"**Active:** {st.session_state.active_dataset_key} ✓")
        
        # Multi-dataset toggles (when multiple datasets loaded)
        if len(dataset_keys) > 1:
            with st.expander("🗂️ All Loaded Datasets", expanded=False):
                st.caption("Toggle datasets to include in analysis context")
                
                # Initialize enabled datasets if not exists
                if "enabled_datasets" not in st.session_state:
                    st.session_state.enabled_datasets = set(dataset_keys)
                
                for ds_key in dataset_keys:
                    ds_info = st.session_state.processed_data[ds_key]
                    ds_df = ds_info["df"]
                    is_active = ds_key == st.session_state.active_dataset_key
                    
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        enabled = st.checkbox(
                            f"{'🟢' if is_active else '⚪'} {ds_key}",
                            value=ds_key in st.session_state.enabled_datasets,
                            key=f"ds_toggle_{ds_key}",
                            disabled=is_active  # Can't disable active dataset
                        )
                        if enabled:
                            st.session_state.enabled_datasets.add(ds_key)
                        else:
                            st.session_state.enabled_datasets.discard(ds_key)
                    with col2:
                        st.caption(f"{ds_df.shape[0]}×{ds_df.shape[1]}")
                
                st.caption(f"📊 {len(st.session_state.enabled_datasets)}/{len(dataset_keys)} datasets enabled")
        
        # Clean data preview
        with st.expander("🔍 Data Preview", expanded=False):
            st.dataframe(active_df.head(10), use_container_width=True)
            st.caption(f"Shape: {active_df.shape[0]} rows × {active_df.shape[1]} columns")
            
        st.download_button(
            label="💾 Download Clean Data",
            data=get_clean_csv_download(active_df),
            file_name=f"cleaned_{st.session_state.active_dataset_key}.csv",
            mime="text/csv",
            use_container_width=True
        )
        
        # Chat Archives UI
        if st.session_state.get("chat_archives"):
            with st.expander(f"📦 Chat Archives ({len(st.session_state.chat_archives)})", expanded=False):
                st.caption("Previous chat sessions are saved here")
                
                for i, archive in enumerate(reversed(st.session_state.chat_archives)):
                    with st.container():
                        st.markdown(f"""
                        <div style='
                            background: rgba(255,255,255,0.05);
                            border-radius: 6px;
                            padding: 8px 10px;
                            margin-bottom: 8px;
                            border-left: 3px solid #666;
                        '>
                            <div style='font-size: 12px; color: #808080;'>
                                📁 {archive['dataset'][:25]}{'...' if len(archive['dataset']) > 25 else ''}
                            </div>
                            <div style='font-size: 11px; color: #606060;'>
                                💬 {archive['message_count']} messages • ⏰ {archive['archived_at']}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("👁️ View", key=f"view_archive_{i}", use_container_width=True):
                                st.session_state[f"show_archive_{i}"] = True
                        with col2:
                            if st.button("🗑️", key=f"del_archive_{i}", use_container_width=True):
                                actual_idx = len(st.session_state.chat_archives) - 1 - i
                                st.session_state.chat_archives.pop(actual_idx)
                                st.rerun()
                        
                        # Show archive content if expanded
                        if st.session_state.get(f"show_archive_{i}"):
                            st.divider()
                            for msg in archive['messages'][:5]:  # Show first 5 messages
                                role_icon = "👤" if msg['role'] == 'user' else "🤖"
                                content_preview = str(msg.get('content', ''))[:100]
                                st.caption(f"{role_icon} {content_preview}...")
                            if len(archive['messages']) > 5:
                                st.caption(f"... and {len(archive['messages']) - 5} more messages")
                            if st.button("Hide", key=f"hide_archive_{i}"):
                                st.session_state[f"show_archive_{i}"] = False
                                st.rerun()
    
    # Add sample datasets section
    add_sample_datasets_section()
    
    # Semantic Search Feature
    st.divider()
    st.subheader("📚 Find Similar Analyses")
    
    with st.expander("ℹ️ How to use this feature", expanded=False):
        st.markdown("""
        **Search your past analyses semantically!**
        
        This feature helps you find similar questions and insights from your previous conversations.
        
        **Examples:**
        - "sales performance by region"
        - "customer satisfaction trends"
        - "profit margins analysis"
        
        **How it works:**
        Your conversations are stored with AI embeddings that understand meaning, not just keywords.
        """)
    
    search_query = st.text_input(
        "🔎 What are you looking for?",
        placeholder="e.g., revenue trends, customer demographics, etc.",
        help="Search across all your past analyses"
    )
    
    if search_query:
        try:
            from utils.vector_db import get_vector_store
            vector_store = get_vector_store()
            
            with st.spinner("🔍 Searching across your analyses..."):
                similar_messages = vector_store.search_similar_messages(search_query, limit=5, min_score=0.6)
            
            if similar_messages:
                st.success(f"✅ Found {len(similar_messages)} similar analyses!")
                for i, msg in enumerate(similar_messages, 1):
                    with st.expander(f"#{i} - {msg['role'].title()} from '{msg['dataset']}' (Match: {msg['score']:.0%})"):
                        st.write(msg['content'][:300] + "..." if len(msg['content']) > 300 else msg['content'])
                        st.caption(f"📅 {msg.get('timestamp', 'Unknown')}")
            else:
                st.info("💡 No similar analyses found. Try different keywords or broader terms.")
        except Exception as e:
            st.warning(f"⚠️ Search feature temporarily unavailable: {str(e)}")

def generate_enhanced_pdf_report(canvas_items, df, include_timestamp):
    """Generate PDF report with embedded charts"""
    from utils.ui_components import generate_pdf_report
    
    pdf_data = generate_pdf_report(canvas_items, df, include_timestamp)
    
    if pdf_data:
        st.download_button(
            label="📄 Download PDF Report",
            data=pdf_data,
            file_name=f"analysis_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mime="application/pdf",
            type="primary"
        )
    
def generate_html_report_download(canvas_items, df, include_timestamp):
    """Generate HTML report with interactive charts"""
    from utils.ui_components import generate_html_report
    
    html_data = generate_html_report(canvas_items, df, include_timestamp)
    
    if html_data:
        st.download_button(
            label="🌐 Download HTML Report",
            data=html_data,
            file_name=f"analysis_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
            mime="text/html",
            type="secondary"
        )

# --- Main View Logic ---
if st.session_state.report_mode:
    # --- REPORT MODE ---
    st.title("📋 Analysis Report")
    
    col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
    with col1:
        if st.button("⬅️ Back to Workshop", use_container_width=True):
            st.session_state.report_mode = False
            st.rerun()
    
    with col2:
        include_timestamp = st.checkbox("Include timestamps", value=False)
    
    # Get current dataset for charts
    current_df = None
    if st.session_state.active_dataset_key and st.session_state.processed_data:
        current_df = st.session_state.processed_data[st.session_state.active_dataset_key]["df"]
    
    with col3:
        if st.session_state.canvas_items and current_df is not None:
            generate_enhanced_pdf_report(st.session_state.canvas_items, current_df, include_timestamp)
    
    with col4:
        if st.session_state.canvas_items and current_df is not None:
            generate_html_report_download(st.session_state.canvas_items, current_df, include_timestamp)
    
    # Display all canvas items
    if st.session_state.canvas_items:
        st.markdown("---")
        
        # Render each canvas item (current_df already fetched above)
        for i, item in enumerate(st.session_state.canvas_items):
            render_canvas_item(item, current_df, i)
    else:
        st.info("📝 Your canvas is empty. Pin some analysis from the workshop first!")

else:
    # --- WORKSHOP MODE ---
    st.markdown("""
    <h1 style='
        color: #E50914;
        font-weight: 900;
        font-size: 42px;
        margin-bottom: 5px;
        letter-spacing: -1px;
    '>
        🚀 OpenAnalyst Workshop
    </h1>
    <p style='color: #808080; margin-bottom: 8px;'>Your AI-powered data analysis workspace with Advanced RAG</p>
    <p style='color: #a0a0a0; font-size: 13px; margin-bottom: 20px;'>
        � <em>Try: "Predict next month's sales" • "Forecast revenue" • "Compare regions" • "What drives growth?"</em>
    </p>
    """, unsafe_allow_html=True)
    
    if not st.session_state.active_dataset_key:
        st.markdown("""
        <div style='
            background: linear-gradient(145deg, #1a1a1a, #252525);
            padding: 40px;
            border-radius: 12px;
            border: 1px solid #333;
            text-align: center;
        '>
            <div style='font-size: 48px; margin-bottom: 15px;'>📚</div>
            <h3 style='color: #fff; margin-bottom: 10px;'>Upload Your Data</h3>
            <p style='color: #808080;'>Drop a CSV or Excel file in the sidebar to begin analysis</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        if st.session_state.active_dataset_key in st.session_state.processed_data:
            active_df = st.session_state.processed_data[st.session_state.active_dataset_key]["df"]
        else:
            st.warning("Selected dataset is not available. Please check your upload.")
            st.stop()
        
        # Tab-based layout with dynamic canvas count
        canvas_count = len(st.session_state.get("canvas_items", []))
        canvas_label = f"📌 Canvas ({canvas_count})" if canvas_count > 0 else "📌 Canvas"
        tab1, tab2, tab3, tab4 = st.tabs(["💬 Chat & Analysis", "📊 Data Preview", canvas_label, "🤖 AI Stats"])
        
        with tab1:
            # Chat & Analysis Tab - Clean Netflix styled header
            st.markdown("""
            <div style='
                background: linear-gradient(135deg, #E50914 0%, #B20710 100%);
                padding: 15px 20px;
                border-radius: 8px;
                margin-bottom: 8px;
                display: flex;
                align-items: center;
                gap: 12px;
            '>
                <span style='font-size: 28px;'>💬</span>
                <div>
                    <h3 style='color: #fff; margin: 0; font-size: 20px;'>Chat with Your Data</h3>
                    <p style='color: rgba(255,255,255,0.8); margin: 0; font-size: 12px;'>Ask questions in natural language • AI-powered analysis</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Show "Generate Analysis" button when no messages (MANUAL trigger - no auto-generation!)
            if not st.session_state.messages:
                # Welcome message and manual trigger
                st.markdown("""
                <div style='
                    background: linear-gradient(145deg, #1a1a1a, #252525);
                    padding: 30px;
                    border-radius: 12px;
                    border: 1px solid #333;
                    text-align: center;
                    margin-bottom: 20px;
                '>
                    <div style='font-size: 36px; margin-bottom: 10px;'>👋</div>
                    <h3 style='color: #fff; margin-bottom: 10px;'>Ready to analyze your data!</h3>
                    <p style='color: #808080;'>Click the button below or ask a question in the chat</p>
                </div>
                """, unsafe_allow_html=True)
                
                col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
                with col_btn2:
                    if st.button("🚀 Generate Analysis", use_container_width=True, type="primary", help="Get an AI overview of your dataset"):
                        st.session_state.messages.append({
                            "role": "user", 
                            "content": f"Welcome! I just loaded the {st.session_state.active_dataset_key} dataset. Please provide:\n1. A brief overview of what's in this data\n2. Key metrics that stand out\n3. Suggest 3 specific, actionable questions I should ask about this data"
                        })
                        st.rerun()
                
                st.markdown("---")
                st.caption("💡 **Tip:** You can also just type a question below to get started!")

            # Chat history with cleaner styling
            for i, msg in enumerate(st.session_state.messages):
                with st.chat_message(msg["role"]):
                    if msg["role"] == "user":
                        st.markdown(msg["content"])
                    else:
                        render_chat_response(msg["content"], active_df, msg_key=i)

            # Handle AI response generation
            if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
                with st.chat_message("assistant"):
                    with st.spinner("🤔 Analyzing..."):
                        try:
                            profile = create_data_profile(active_df, st.session_state.active_dataset_key)
                            history = st.session_state.messages
                            
                            # Pass domain info and user_id to AI (HYBRID MODEL!)
                            # Also pass df for smart query routing (cost optimization!)
                            domain_info = st.session_state.get('current_domain_info', {})
                            current_user_id = st.session_state.get('username', 'anonymous')
                            ai_response = get_ai_response(profile, history, domain_info=domain_info, user_id=current_user_id, df=active_df)
                            
                            if not isinstance(ai_response, dict):
                                ai_response = {"content": str(ai_response), "suggested_actions": []}
                            
                            st.session_state.messages.append({"role": "assistant", "content": ai_response})
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"Analysis failed: {str(e)}")
                            st.session_state.messages.append({
                                "role": "assistant", 
                                "content": {"content": "I encountered an error while analyzing the data. Please try again.", "suggested_actions": []}
                            })
            
            # User input
            if prompt := st.chat_input("Ask a follow-up question..."):
                st.session_state.messages.append({"role": "user", "content": prompt})
                st.rerun()
        
        with tab2:
            # Data Preview Tab
            st.subheader("Data Preview")
            
            # Get raw data and derived columns from processed data
            dataset_info = st.session_state.processed_data[st.session_state.active_dataset_key]
            raw_df = dataset_info.get("raw_df", active_df)  # Fallback to active_df if not available
            derived_columns = dataset_info.get("derived_columns", [])
            
            # Import and render data quality dashboard
            from utils.data_preview_components import (
                render_data_quality_dashboard,
                show_cleaning_impact_modal,
                show_quality_breakdown_modal,
                show_derivation_logic_modal,
                show_raw_data_modal,
                show_cleaned_data_modal
            )
            from utils.data_quality import get_cleaning_stats, calculate_data_quality_score
            
            # Render main dashboard
            render_data_quality_dashboard(raw_df, active_df, derived_columns)
            
            st.markdown("---")
            
            # File selector and current file indicator
            dataset_keys = list(st.session_state.processed_data.keys())
            if len(dataset_keys) > 1:
                st.markdown("### 📂 Select Dataset to Preview")
                col1, col2 = st.columns([3, 1])
                with col1:
                    selected_preview_dataset = st.selectbox(
                        "Choose dataset:",
                        options=dataset_keys,
                        index=dataset_keys.index(st.session_state.active_dataset_key) if st.session_state.active_dataset_key in dataset_keys else 0,
                        key="preview_dataset_selector"
                    )
                with col2:
                    if selected_preview_dataset != st.session_state.active_dataset_key:
                        if st.button("🔄 Switch Dataset", type="primary"):
                            st.session_state.active_dataset_key = selected_preview_dataset
                            st.session_state.messages = []
                            st.rerun()
                
                # Update active_df if different dataset selected for preview only
                if selected_preview_dataset != st.session_state.active_dataset_key:
                    preview_df = st.session_state.processed_data[selected_preview_dataset]["df"]
                    st.info(f"👀 Previewing: **{selected_preview_dataset}** (Click 'Switch Dataset' to analyze this data)")
                else:
                    preview_df = active_df
                    st.success(f"✅ Currently analyzing: **{st.session_state.active_dataset_key}**")
            else:
                preview_df = active_df
                st.info(f"📊 Exploring: **{st.session_state.active_dataset_key}**")
            
            st.markdown("")
            
            # Before/After Cleaning Comparison View
            st.markdown("### 🔄 Data Comparison: Original vs Cleaned")
            
            view_mode = st.radio(
                "Select view:",
                options=["Cleaned Data (Recommended)", "Original Data", "Side-by-Side Comparison"],
                horizontal=True,
                help="Compare original uploaded data with AI-cleaned version"
            )
            
            if view_mode == "Side-by-Side Comparison":
                # Show both datasets side by side
                col_before, col_after = st.columns(2)
                
                with col_before:
                    st.markdown("#### 📥 Original Data")
                    st.caption(f"Rows: {len(raw_df):,} | Columns: {len(raw_df.columns)}")
                    st.dataframe(raw_df.head(10), use_container_width=True, height=400)
                    
                    # Show issues in original data
                    with st.expander("⚠️ Data Issues Found"):
                        cleaning_stats = get_cleaning_stats(raw_df, preview_df)
                        if cleaning_stats['missing']['before'] > 0:
                            st.warning(f"🔴 {cleaning_stats['missing']['before']:,} missing values")
                        if cleaning_stats['duplicates']['before'] > 0:
                            st.warning(f"🔴 {cleaning_stats['duplicates']['before']:,} duplicate rows")
                        if cleaning_stats['rows']['change'] < 0:
                            st.warning(f"🔴 {abs(cleaning_stats['rows']['change']):,} empty rows")
                
                with col_after:
                    st.markdown("#### ✨ Cleaned Data")
                    st.caption(f"Rows: {len(preview_df):,} | Columns: {len(preview_df.columns)}")
                    st.dataframe(preview_df.head(10), use_container_width=True, height=400)
                    
                    # Show improvements
                    with st.expander("✅ Cleaning Applied"):
                        if cleaning_stats['missing']['change'] < 0:
                            st.success(f"✅ Removed {abs(cleaning_stats['missing']['change']):,} missing values")
                        if cleaning_stats['duplicates']['change'] < 0:
                            st.success(f"✅ Removed {abs(cleaning_stats['duplicates']['change']):,} duplicates")
                        if cleaning_stats['rows']['change'] < 0:
                            st.success(f"✅ Removed {abs(cleaning_stats['rows']['change']):,} empty rows")
                        if len(derived_columns) > 0:
                            st.success(f"✅ Added {len(derived_columns)} derived columns")
                
                st.markdown("---")
            
            elif view_mode == "Original Data":
                # Show only original data
                display_df = raw_df
                st.warning("⚠️ Viewing original unprocessed data - may contain errors, duplicates, and missing values")
            else:
                # Show cleaned data (default)
                display_df = preview_df
                cleaning_stats = get_cleaning_stats(raw_df, preview_df)
                if cleaning_stats['rows']['change'] != 0 or cleaning_stats['missing']['change'] != 0:
                    st.success(f"✅ Data has been cleaned: {abs(cleaning_stats['rows']['change'])} rows removed, {abs(cleaning_stats['missing']['change'])} missing values handled")
            
            # Enhanced data table with missing data percentages in column headers
            if view_mode != "Side-by-Side Comparison":
                # Calculate missing percentages for each column
                total_rows = len(display_df)
                col_stats = []
                for col in display_df.columns:
                    non_null_count = display_df[col].count()
                    null_count = display_df[col].isnull().sum()
                    missing_pct = (null_count / total_rows * 100) if total_rows > 0 else 0
                    col_stats.append({
                        'column': col,
                        'non_null': non_null_count,
                        'missing_pct': missing_pct
                    })
                
                # Display column headers with missing data info
                st.markdown("#### 📊 Data Table")
                if any(stat['missing_pct'] > 0 for stat in col_stats):
                    st.caption("💡 Column headers show: **Values (Missing%)**")
                
                # Create a formatted dataframe with enhanced column names
                formatted_df = display_df.copy()
                formatted_df.columns = [
                    f"{stat['column']} - {int(stat['non_null'])} ({stat['missing_pct']:.1f}% missing)" 
                    if stat['missing_pct'] > 0 
                    else f"{stat['column']} - {int(stat['non_null'])}"
                    for stat in col_stats
                ]
                
                st.dataframe(formatted_df, use_container_width=True, height=500)
            
            # Column info (only show for single view modes)
            if view_mode != "Side-by-Side Comparison":
                with st.expander("📋 Detailed Column Information"):
                    col_info = pd.DataFrame({
                        "Column": display_df.columns,
                        "Type": display_df.dtypes.astype(str),
                        "Non-Null Count": display_df.count(),
                        "Null Count": display_df.isnull().sum(),
                        "Missing %": [f"{(display_df[col].isnull().sum() / len(display_df) * 100):.1f}%" for col in display_df.columns],
                        "Unique Values": [display_df[col].nunique() for col in display_df.columns]
                    })
                    st.dataframe(col_info, use_container_width=True)
            
            # Handle modal dialogs
            if st.session_state.get("show_cleaning_impact", False):
                cleaning_stats = get_cleaning_stats(raw_df, active_df)
                show_cleaning_impact_modal(raw_df, active_df, cleaning_stats)
                st.session_state.show_cleaning_impact = False
            
            if st.session_state.get("show_quality_breakdown", False):
                quality_data = calculate_data_quality_score(raw_df, active_df, derived_columns)
                show_quality_breakdown_modal(quality_data)
                st.session_state.show_quality_breakdown = False
            
            if st.session_state.get("show_derivation_modal", False):
                show_derivation_logic_modal(raw_df, active_df, derived_columns)
                st.session_state.show_derivation_modal = False
            
            if st.session_state.get("show_raw_table", False):
                show_raw_data_modal(raw_df)
                st.session_state.show_raw_table = False
            
            if st.session_state.get("show_cleaned_table", False):
                show_cleaned_data_modal(active_df)
                st.session_state.show_cleaned_table = False
        
        with tab3:
            # Canvas Tab
            col_header1, col_header2, col_header3 = st.columns([2, 1, 1])
            with col_header1:
                st.subheader("📌 Canvas")
            with col_header2:
                if st.button("🆕 New Canvas", use_container_width=True, help="Start a fresh canvas"):
                    if st.session_state.canvas_items:
                        # Add confirmation via session state
                        st.session_state.show_clear_canvas_confirm = True
            with col_header3:
                if st.session_state.canvas_items:
                    if st.button("📋 Finalize Report", type="primary", use_container_width=True):
                        st.session_state.report_mode = True
                        st.rerun()
            
            # Confirmation dialog for clearing canvas
            if st.session_state.get("show_clear_canvas_confirm", False):
                st.warning("⚠️ **Are you sure you want to start a new canvas?** This will clear all pinned items.")
                col1, col2, col3 = st.columns([1, 1, 2])
                with col1:
                    if st.button("✅ Yes, Clear", type="primary"):
                        st.session_state.canvas_items = []
                        st.session_state.show_clear_canvas_confirm = False
                        st.success("Canvas cleared!")
                        st.rerun()
                with col2:
                    if st.button("❌ Cancel"):
                        st.session_state.show_clear_canvas_confirm = False
                        st.rerun()
            
            # Canvas content
            if not st.session_state.canvas_items:
                st.info("💡 Pin insights and charts from the Chat tab to build your report!\n\n**How to use:**\n1. Ask questions in the Chat tab\n2. Click '📌 Add to Canvas' on useful responses\n3. Click '📋 Finalize Report' to export as PDF/HTML")
            else:
                st.caption(f"📊 **{len(st.session_state.canvas_items)} items pinned** - Drag to reorder coming soon!")
                st.markdown("---")
                
                # Create a scrollable container for canvas items (compressed view)
                for i, item in enumerate(st.session_state.canvas_items):
                    render_canvas_item(item, active_df, i)
        
        with tab4:
            # AI Stats Tab
            st.subheader("🤖 AI Usage & Performance")
            st.markdown("Track your AI interactions, token usage, and system performance")
            
            # Initialize AI stats if not exists
            if 'ai_stats' not in st.session_state:
                st.session_state.ai_stats = {
                    'total_queries': 0,
                    'total_input_tokens': 0,
                    'total_output_tokens': 0,
                    'total_embeddings': 0,
                    'queries_by_type': {'text': 0, 'visualization': 0, 'analysis': 0},
                    'avg_response_time': 0,
                    'session_start': datetime.datetime.now()
                }
            
            stats = st.session_state.ai_stats
            
            # Overview metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Total Queries",
                    f"{stats['total_queries']:,}",
                    help="Number of questions asked to AI this session"
                )
            
            with col2:
                total_tokens = stats['total_input_tokens'] + stats['total_output_tokens']
                st.metric(
                    "Total Tokens",
                    f"{total_tokens:,}",
                    help="Combined input and output tokens used"
                )
            
            with col3:
                st.metric(
                    "Embeddings Created",
                    f"{stats['total_embeddings']:,}",
                    help="Vector embeddings stored for semantic search"
                )
            
            with col4:
                if stats['total_queries'] > 0:
                    avg_time = stats['avg_response_time']
                    st.metric(
                        "Avg Response Time",
                        f"{avg_time:.2f}s",
                        help="Average time to generate AI responses"
                    )
                else:
                    st.metric("Avg Response Time", "N/A")
            
            st.markdown("---")
            
            # Token breakdown
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 📊 Token Usage Breakdown")
                
                if total_tokens > 0:
                    # Create token breakdown chart
                    token_data = pd.DataFrame({
                        'Type': ['Input Tokens', 'Output Tokens'],
                        'Count': [stats['total_input_tokens'], stats['total_output_tokens']]
                    })
                    
                    import plotly.express as px
                    fig = px.pie(token_data, values='Count', names='Type', 
                                title='Token Distribution',
                                color_discrete_sequence=['#636EFA', '#EF553B'])
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Estimated cost (Gemini Flash pricing: ~$0.075 per 1M input tokens, ~$0.30 per 1M output)
                    input_cost = (stats['total_input_tokens'] / 1_000_000) * 0.075
                    output_cost = (stats['total_output_tokens'] / 1_000_000) * 0.30
                    total_cost = input_cost + output_cost
                    
                    st.info(f"**💰 Estimated Cost:** ${total_cost:.4f} (Gemini Flash-Lite rates)")
                    st.caption(f"Input: {stats['total_input_tokens']:,} tokens (${input_cost:.4f})")
                    st.caption(f"Output: {stats['total_output_tokens']:,} tokens (${output_cost:.4f})")
                else:
                    st.info("No tokens used yet. Start asking questions!")
            
            with col2:
                st.markdown("### 📈 Query Types")
                
                query_types = stats['queries_by_type']
                if sum(query_types.values()) > 0:
                    # Create query type breakdown chart
                    query_data = pd.DataFrame({
                        'Type': ['Text Response', 'Visualization', 'Data Analysis'],
                        'Count': [query_types['text'], query_types['visualization'], query_types['analysis']]
                    })
                    query_data = query_data[query_data['Count'] > 0]  # Filter out zeros
                    
                    import plotly.express as px
                    fig = px.bar(query_data, x='Type', y='Count',
                                title='Queries by Response Type',
                                color='Type',
                                color_discrete_sequence=['#00CC96', '#AB63FA', '#FFA15A'])
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No queries yet. Start chatting!")
            
            st.markdown("---")
            
            # Session info
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### ⏱️ Session Information")
                session_duration = datetime.datetime.now() - stats['session_start']
                hours, remainder = divmod(session_duration.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                
                st.write(f"**Session Duration:** {hours}h {minutes}m {seconds}s")
                st.write(f"**Session Started:** {stats['session_start'].strftime('%Y-%m-%d %H:%M:%S')}")
                st.write(f"**Active Model:** {st.session_state.get('selected_model', 'Unknown')}")
            
            with col2:
                st.markdown("### 🎯 Performance Insights")
                
                if stats['total_queries'] > 0:
                    tokens_per_query = total_tokens / stats['total_queries']
                    st.write(f"**Avg Tokens per Query:** {tokens_per_query:.0f}")
                    
                    if stats['avg_response_time'] < 2:
                        st.success("✅ Excellent response times!")
                    elif stats['avg_response_time'] < 5:
                        st.info("✅ Good response times")
                    else:
                        st.warning("⚠️ Response times could be improved")
                    
                    efficiency_score = min(100, int((10000 / tokens_per_query) * 10))
                    st.progress(efficiency_score / 100)
                    st.caption(f"Query Efficiency Score: {efficiency_score}/100")
                else:
                    st.info("Start using the AI to see performance insights")
            
            st.markdown("---")
            
            # Vector DB stats (if enabled)
            try:
                from utils.vector_db import VECTOR_DB_ENABLED
                vector_db_available = VECTOR_DB_ENABLED
            except ImportError:
                vector_db_available = False
            
            if vector_db_available:
                st.markdown("### 🗄️ Vector Database Status")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Status", "🟢 Connected", help="Qdrant Cloud vector database")
                
                with col2:
                    st.metric("Embeddings Stored", f"{stats['total_embeddings']:,}")
                
                with col3:
                    st.metric("Semantic Search", "✅ Enabled")
                
                st.caption("💡 Your conversations are being stored for semantic search. Find similar past analyses instantly!")
            else:
                st.markdown("### 🗄️ Vector Database Status")
                st.warning("⚠️ Vector database not configured. Semantic search unavailable.")
                st.caption("Configure Qdrant to enable semantic search of past analyses.")

# Debug footer (only visible in debug mode)
if DEBUG_MODE:
    st.sidebar.markdown("---")
    st.sidebar.markdown("🔧 **Debug Info:**")
    st.sidebar.write(f"Messages: {len(st.session_state.messages)}")
    st.sidebar.write(f"Canvas Items: {len(st.session_state.canvas_items)}")
    if st.session_state.processed_data:
        st.sidebar.write(f"Datasets: {list(st.session_state.processed_data.keys())}")