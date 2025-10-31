import streamlit as st
from utils.data_handler import read_and_clean_files, get_clean_csv_download, create_data_profile
from utils.ai_core import get_ai_response
from utils.ui_components import render_chat_response, render_canvas_item

# Set the page configuration for a wide layout and a professional title.
st.set_page_config(layout="wide", page_title="Open Analyst Workshop")

# --- Debug Mode Toggle (Hidden - only accessible via URL parameter) ---
# Access with: http://localhost:8501/?debug=true
ADMIN_MODE = st.query_params.get("admin", "false").lower() == "true"

if ADMIN_MODE:
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 🔧 Admin Panel")
        
        # Test Ollama connection
        try:
            import ollama
            models = ollama.list()
            st.success("✅ Ollama connected")
            st.json({"models": models})
        except Exception as e:
            st.error(f"❌ Ollama error: {str(e)}")
        
        # Session info
        st.markdown("**Session State:**")
        st.json({
            "messages": len(st.session_state.messages),
            "canvas_items": len(st.session_state.canvas_items),
            "active_dataset": st.session_state.active_dataset_key
        })
DEBUG_MODE = st.query_params.get("debug", "false").lower() == "true"

def debug_log(message):
    """Only shows debug messages if debug mode is enabled"""
    if DEBUG_MODE:
        st.write(message)

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
    st.title("Data Context")
    
    uploaded_files = st.file_uploader(
        "Upload Files", type=["csv", "xlsx"], accept_multiple_files=True
    )
    
    # Only process if files have changed
    if uploaded_files:
        current_file_names = tuple(f.name for f in uploaded_files)
        
        # Check if these are NEW files
        if current_file_names != st.session_state.last_uploaded_files:
            debug_log("🔍 New files detected, processing...")
            try:
                st.session_state.messages = []
                st.session_state.canvas_items = []
                st.session_state.processed_data = read_and_clean_files(tuple(uploaded_files))
                st.session_state.last_uploaded_files = current_file_names
                debug_log(f"✅ Processed {len(st.session_state.processed_data)} datasets")
            except Exception as e:
                st.error(f"Failed to process files: {e}")
    
    if st.session_state.processed_data:
        dataset_keys = list(st.session_state.processed_data.keys())
        st.session_state.active_dataset_key = st.radio("Select Dataset:", dataset_keys)
        active_df = st.session_state.processed_data[st.session_state.active_dataset_key]
        
        with st.expander("Show Data Preview", expanded=False):
            st.dataframe(active_df.head())
            
        st.download_button(
            label="Download Clean Data",
            data=get_clean_csv_download(active_df),
            file_name=f"cleaned_{st.session_state.active_dataset_key}.csv",
            mime="text/csv"
        )

# --- Main View Logic ---
if st.session_state.report_mode:
    # --- REPORT MODE ---
    st.title("📋 Finalize Report")
    if st.button("⬅️ Back to Workshop"):
        st.session_state.report_mode = False
        st.rerun()
    
    active_df = st.session_state.processed_data.get(st.session_state.active_dataset_key)
    if active_df is not None and st.session_state.canvas_items:
        for i, item in enumerate(st.session_state.canvas_items):
            render_canvas_item(item, active_df, i)
    else:
        st.warning("Your canvas is empty or no data is loaded.")
        
else:
    # --- WORKSHOP MODE ---
    st.title("🚀 Open Analyst Workshop")
    
    if not st.session_state.active_dataset_key:
        st.info("Please upload a file to begin your analysis.")
    else:
        col1, col2 = st.columns(2, gap="large")
        active_df = st.session_state.processed_data[st.session_state.active_dataset_key]

        with col1:
            st.subheader("Chat & Analysis")
            
            # Show "Generate Initial Summary" button if no messages
            if not st.session_state.messages:
                if st.button("Generate Initial Summary", use_container_width=True, type="primary"):
                    st.session_state.messages.append({
                        "role": "user", 
                        "content": "Generate a brief, initial summary of the data, focusing on key metrics and potential areas of interest."
                    })
                    st.rerun()

            # Display chat history
            for i, msg in enumerate(st.session_state.messages):
                with st.chat_message(msg["role"]):
                    if msg["role"] == "user":
                        st.markdown(msg["content"])
                    else:
                        render_chat_response(msg["content"], active_df, msg_key=i)

            # Handle AI response generation
            if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
                with st.chat_message("assistant"):
                    with st.spinner("Analyzing..."):
                        try:
                            profile = create_data_profile(active_df, st.session_state.active_dataset_key)
                            history = st.session_state.messages
                            ai_response = get_ai_response(profile, history)
                            
                            # Validate response
                            if not isinstance(ai_response, dict):
                                ai_response = {
                                    "response_type": "error",
                                    "content": "I had trouble processing that request. Could you try asking in a different way?",
                                    "is_visualizable": False,
                                    "suggested_actions": ["Try rephrasing", "Ask a different question"]
                                }
                            
                            st.session_state.messages.append({"role": "assistant", "content": ai_response})
                            st.rerun()
                            
                        except Exception as e:
                            error_response = {
                                "response_type": "error",
                                "content": "I encountered an issue while analyzing your data. Please try again.",
                                "is_visualizable": False,
                                "suggested_actions": ["Try again", "Ask a different question"]
                            }
                            st.session_state.messages.append({"role": "assistant", "content": error_response})
                            st.rerun()
            
            # User chat input
            if prompt := st.chat_input("Ask a follow-up question..."):
                st.session_state.messages.append({"role": "user", "content": prompt})
                st.rerun()

        with col2:
            st.subheader("Canvas")
            if st.button("📋 Finalize Report"):
                st.session_state.report_mode = True
                st.rerun()
                
            if not st.session_state.canvas_items:
                st.info("Click '➕ Pin' on an insight to build your report.")
            else:
                for i, item in enumerate(st.session_state.canvas_items):
                    render_canvas_item(item, active_df, i)

# Debug footer (only visible in debug mode)
if DEBUG_MODE:
    st.markdown("---")
    st.markdown("### 🐛 Debug Panel")
    st.json({
        "messages_count": len(st.session_state.messages),
        "canvas_items": len(st.session_state.canvas_items),
        "active_dataset": st.session_state.active_dataset_key,
        "last_uploaded": st.session_state.last_uploaded_files
    })