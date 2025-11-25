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
st.set_page_config(layout="wide", page_title="Open Analyst Workshop", initial_sidebar_state="expanded")

# Custom CSS to ensure text visibility in both light and dark modes
st.markdown("""
<style>
    /* Ensure text is visible in all system themes (light/dark) */
    .stMarkdown, .stMarkdown p, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: inherit !important;
    }
    
    /* Force high contrast for step headers */
    div[data-testid="stMarkdownContainer"] h2,
    div[data-testid="stMarkdownContainer"] h3 {
        opacity: 1 !important;
        filter: none !important;
    }
    
    /* Ensure subheaders are always visible */
    .stMarkdown h3 {
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# --- Authentication Check ---
if not check_authentication():
    # Enhanced landing page with modern design
    st.markdown("""
    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px; border-radius: 10px; margin-bottom: 30px;'>
        <h1 style='text-align: center; color: white; font-size: 48px; margin-bottom: 10px;'>
            � OpenAnalyst
        </h1>
        <h3 style='text-align: center; color: #f0f0f0; font-weight: 300; margin-bottom: 5px;'>
            AI-Powered Data Analysis Platform
        </h3>
        <p style='text-align: center; color: #e0e0e0; font-size: 16px;'>
            Transform your data into insights with advanced AI. No coding required.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Two-column layout: Login OR Try Demo
    col_left, col_right = st.columns([1, 1], gap="large")
    
    with col_left:
        st.markdown("### � Login to Your Account")
        st.markdown("Upload your own data and get unlimited AI analysis")
        
        render_login()
    
    with col_right:
        st.markdown("### 🎯 Try Without Login")
        st.markdown("Explore OpenAnalyst with sample datasets")
        st.markdown("")
        
        # Sample data buttons with better styling
        sample_datasets = [
            ("🛒 E-commerce Sales", "sample_ecommerce_sales.csv", "Sales trends, product performance, customer behavior"),
            ("😊 Customer Survey", "sample_customer_survey.csv", "Satisfaction scores, feedback patterns, sentiment analysis"),
            ("� Financial Metrics", "sample_financial_metrics.csv", "Financial KPIs, budget tracking, forecasting")
        ]
        
        for icon_name, filename, description in sample_datasets:
            with st.container():
                col_icon, col_content = st.columns([0.15, 0.85])
                with col_icon:
                    st.markdown(f"### {icon_name.split()[0]}")
                with col_content:
                    st.markdown(f"**{icon_name.split(' ', 1)[1]}**")
                    st.caption(description)
                
                if st.button(f"Try {icon_name}", key=filename, use_container_width=True, type="secondary"):
                    # Auto-login as demo user
                    st.session_state['authenticated'] = True
                    st.session_state['username'] = 'demo_user'
                    st.session_state['name'] = 'Demo User'
                    st.session_state['authentication_status'] = True
                    
                    # Set loading state for sample data
                    st.session_state.demo_sample = filename
                    st.session_state.demo_sample_name = icon_name
                    st.session_state.loading_sample = True
                    st.rerun()
                
                st.markdown("")
    
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 20px;'>
        <p><strong>How it works:</strong></p>
        <p>� Upload/Select Data → 💬 Ask Questions in Natural Language → 📈 Get AI-Powered Insights → 📄 Export Reports</p>
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
    try:
        from utils.vector_db import ensure_samples_indexed
        ensure_samples_indexed()
        st.session_state.vector_db_initialized = True
    except Exception as e:
        # Silent fail - vector DB is optional
        st.session_state.vector_db_initialized = False

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
    st.title("📊 Data Context")
    
    # Model Selector
    st.divider()
    st.subheader("🤖 AI Model")
    
    # Available models with status
    model_options = {
        "gemini-2.5-flash": "Gemini Flash (Fast, Balanced)",
        "gemini-2.5-flash-lite": "Gemini Flash Lite (Current, Free)",
        "gemini-2.5-flash-8b": "Gemini Flash-8B (Efficient)",
        "gpt-4": "GPT-4 (No API Connected)",
        "claude-3": "Claude 3 (No API Connected)"
    }
    
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
        # Check if it's a non-Gemini model
        if selected_model in ["gpt-4", "claude-3"]:
            st.warning("🔌 No API connected for this model. Please use Gemini models.")
            # Revert selection
            st.session_state.selected_model = st.session_state.selected_model
        else:
            # Update model
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
            from utils.domain_detector import detect_data_domain
            from utils.vector_db import get_vector_store
            from utils.similar_analyses_widget import render_similar_analyses_widget
            from utils.seed_vector_db import seed_vector_db
            
            # Get active dataframe
            active_df = st.session_state.processed_data[st.session_state.active_dataset_key]["df"]
            
            # Detect domain (cache it in session state)
            if 'current_domain_info' not in st.session_state or st.session_state.previous_dataset_key != st.session_state.active_dataset_key:
                domain_info = detect_data_domain(active_df)
                st.session_state.current_domain_info = domain_info
            else:
                domain_info = st.session_state.current_domain_info
            
            # Seed vector DB on first load
            if 'vector_db_seeded' not in st.session_state:
                seed_vector_db()
                st.session_state.vector_db_seeded = True
            
            # Render similar analyses widget
            vector_store = get_vector_store()
            render_similar_analyses_widget(
                vector_store=vector_store,
                current_domain=domain_info['domain'],
                current_dataset_name=st.session_state.active_dataset_key
            )
            
        except Exception as e:
            logger.error(f"Error rendering similar analyses: {e}")
            st.divider()
    
    uploaded_files = st.file_uploader(
        "Upload Files", type=["csv", "xlsx"], accept_multiple_files=True
    )
    
    # Only process if files have changed
    if uploaded_files:
        current_file_names = tuple(f.name for f in uploaded_files)
        
        if current_file_names != st.session_state.last_uploaded_files:
            debug_log("🔍 New files detected, processing...")
            try:
                st.session_state.messages = []
                # DON'T clear canvas_items - this keeps them persistent
                st.session_state.processed_data = read_and_clean_files(tuple(uploaded_files))
                st.session_state.last_uploaded_files = current_file_names
                debug_log(f"✅ Processed {len(st.session_state.processed_data)} datasets")
            except Exception as e:
                st.error(f"Failed to process files: {e}")
    
    if st.session_state.processed_data:
        dataset_keys = list(st.session_state.processed_data.keys())
        
        # Track previous dataset to detect changes
        if "previous_dataset_key" not in st.session_state:
            st.session_state.previous_dataset_key = st.session_state.active_dataset_key
        
        # Radio button for dataset selection
        selected_dataset = st.radio("📁 Select Dataset:", dataset_keys, 
                                    index=dataset_keys.index(st.session_state.active_dataset_key) if st.session_state.active_dataset_key in dataset_keys else 0)
        
        # Detect dataset change
        if selected_dataset != st.session_state.active_dataset_key and st.session_state.messages:
            st.warning("⚠️ **Switching datasets will clear your chat history** (Canvas is preserved)")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Switch & Clear Chat", type="primary", use_container_width=True):
                    st.session_state.active_dataset_key = selected_dataset
                    st.session_state.messages = []
                    st.session_state.previous_dataset_key = selected_dataset
                    st.success(f"Switched to {selected_dataset}")
                    st.rerun()
            with col2:
                if st.button("❌ Cancel", use_container_width=True):
                    # Keep current dataset
                    st.rerun()
        elif selected_dataset != st.session_state.active_dataset_key:
            # No chat history, switch immediately
            st.session_state.active_dataset_key = selected_dataset
            st.session_state.previous_dataset_key = selected_dataset
        
        active_df = st.session_state.processed_data[st.session_state.active_dataset_key]["df"]
        
        # Visual indicator for active dataset
        st.success(f"**Active:** {st.session_state.active_dataset_key} ✓")
        
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
    
    # Add sample datasets section
    add_sample_datasets_section()
    
    # Semantic Search Feature
    st.divider()
    st.subheader("� Find Similar Analyses")
    
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
    st.title("🚀 Open Analyst Workshop")
    
    if not st.session_state.active_dataset_key:
        st.info("👆 Please upload a file to begin your analysis.")
    else:
        if st.session_state.active_dataset_key in st.session_state.processed_data:
            active_df = st.session_state.processed_data[st.session_state.active_dataset_key]["df"]
        else:
            st.warning("Selected dataset is not available. Please check your upload.")
            st.stop()
        
        # Tab-based layout
        tab1, tab2, tab3, tab4 = st.tabs(["💬 Chat & Analysis", "📊 Data Preview", "📌 Canvas", "🤖 AI Stats"])
        
        with tab1:
            # Chat & Analysis Tab
            st.subheader("Chat & Analysis")
            
            # Auto-generate initial summary when dataset first loads
            if not st.session_state.messages:
                # Check if we need to generate initial prompt for this dataset
                if 'initial_prompt_generated' not in st.session_state:
                    st.session_state.initial_prompt_generated = set()
                
                if st.session_state.active_dataset_key not in st.session_state.initial_prompt_generated:
                    # Auto-trigger initial summary
                    st.session_state.messages.append({
                        "role": "user", 
                        "content": f"Welcome! I just loaded the {st.session_state.active_dataset_key} dataset. Please provide:\n1. A brief overview of what's in this data\n2. Key metrics that stand out\n3. Suggest 3 specific, actionable questions I should ask about this data"
                    })
                    st.session_state.initial_prompt_generated.add(st.session_state.active_dataset_key)
                    st.rerun()
                else:
                    # Show manual trigger button if messages were cleared but dataset was already initialized
                    if st.button("🎯 Generate Initial Summary", use_container_width=True, type="primary"):
                        st.session_state.messages.append({
                            "role": "user", 
                            "content": f"Welcome! I just loaded the {st.session_state.active_dataset_key} dataset. Please provide:\n1. A brief overview of what's in this data\n2. Key metrics that stand out\n3. Suggest 3 specific, actionable questions I should ask about this data"
                        })
                        st.rerun()

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
                            
                            # Pass domain info to AI if available
                            domain_info = st.session_state.get('current_domain_info', {})
                            ai_response = get_ai_response(profile, history, domain_info=domain_info)
                            
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