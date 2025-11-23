from utils.data_handler import read_and_clean_files, get_clean_csv_download, create_data_profile
from utils.ai_core import get_ai_response
from utils.ui_components import render_chat_response, render_canvas_item
import streamlit as st
import pandas as pd
import datetime

# Set the page configuration for a wide layout and a professional title.
st.set_page_config(layout="wide", page_title="Open Analyst Workshop")

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
        st.session_state.active_dataset_key = st.radio("📁 Select Dataset:", dataset_keys)
        active_df = st.session_state.processed_data[st.session_state.active_dataset_key]["df"]
        
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

def generate_enhanced_pdf_report(canvas_items, include_timestamp):
    """Generate a properly formatted PDF report"""
    
    # Create a clean, formatted report content
    report_content = "# Data Analysis Report\n\n"
    
    if include_timestamp:
        report_content += f"**Generated:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    report_content += "---\n\n"
    
    # Add each canvas item with proper formatting
    for i, item in enumerate(canvas_items, 1):
        title = item.get("title", f"Analysis {i}")
        text_content = item.get("text_content", "")
        dataset_source = item.get("dataset_source", "Unknown")
        timestamp = item.get("timestamp", "Unknown")
        
        report_content += f"## {i}. {title}\n\n"
        
        # Add metadata
        report_content += f"**Dataset:** {dataset_source}  \n"
        if include_timestamp:
            report_content += f"**Added:** {timestamp}  \n"
        report_content += "\n"
        
        # Add content
        if text_content:
            report_content += f"{text_content}\n\n"
        
        # Add chart info if available
        if item.get("chart_data"):
            chart_data = item["chart_data"]
            chart_title = chart_data.get("title", "Visualization")
            chart_type = chart_data.get("chart_type", "chart")
            report_content += f"**Visualization:** {chart_title} ({chart_type})\n\n"
        
        report_content += "---\n\n"
    
    # Download as markdown file (which can be easily converted to PDF)
    st.download_button(
        label="📄 Download Report",
        data=report_content,
        file_name=f"analysis_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
        mime="text/markdown"
    )

# --- Main View Logic ---
if st.session_state.report_mode:
    # --- REPORT MODE ---
    st.title("📋 Analysis Report")
    
    col1, col2, col3 = st.columns([2, 2, 2])
    with col1:
        if st.button("⬅️ Back to Workshop", use_container_width=True):
            st.session_state.report_mode = False
            st.rerun()
    
    with col2:
        include_timestamp = st.checkbox("Include timestamps in PDF", value=False)
    
    with col3:
        if st.session_state.canvas_items:
            if st.button("📄 Download PDF Report", type="primary", use_container_width=True):
                generate_enhanced_pdf_report(st.session_state.canvas_items, include_timestamp)
    
    # Display all canvas items
    if st.session_state.canvas_items:
        st.markdown("---")
        
        # Get current dataset for chart rendering (if available)
        current_df = None
        if st.session_state.active_dataset_key and st.session_state.processed_data:
            current_df = st.session_state.processed_data[st.session_state.active_dataset_key]["df"]
        
        # Render each canvas item
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
        col1, col2 = st.columns([1, 1], gap="large")
        
        if st.session_state.active_dataset_key in st.session_state.processed_data:
            active_df = st.session_state.processed_data[st.session_state.active_dataset_key]["df"]
        else:
            st.warning("Selected dataset is not available. Please check your upload.")
            st.stop()

        with col1:
            st.subheader("💬 Chat & Analysis")
            
            # Generate Initial Summary button
            if not st.session_state.messages:
                if st.button("🎯 Generate Initial Summary", use_container_width=True, type="primary"):
                    st.session_state.messages.append({
                        "role": "user", 
                        "content": "Generate a brief, initial summary of the data, focusing on key metrics and potential areas of interest."
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
                            ai_response = get_ai_response(profile, history)
                            
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

        with col2:
            # Canvas header with report button
            col_header1, col_header2 = st.columns([2, 1])
            with col_header1:
                st.subheader("📌 Canvas")
            with col_header2:
                if st.session_state.canvas_items:
                    if st.button("📋 View Report", type="secondary", use_container_width=True):
                        st.session_state.report_mode = True
                        st.rerun()
            
            # Canvas content
            if not st.session_state.canvas_items:
                st.info("💡 Pin charts from your analysis to build a report!")
            else:
                st.caption(f"📊 {len(st.session_state.canvas_items)} items pinned")
                
                # Create a scrollable container for canvas items
                with st.container():
                    for i, item in enumerate(st.session_state.canvas_items):
                        render_canvas_item(item, active_df, i)

# Debug footer (only visible in debug mode)
if DEBUG_MODE:
    st.sidebar.markdown("---")
    st.sidebar.markdown("🔧 **Debug Info:**")
    st.sidebar.write(f"Messages: {len(st.session_state.messages)}")
    st.sidebar.write(f"Canvas Items: {len(st.session_state.canvas_items)}")
    if st.session_state.processed_data:
        st.sidebar.write(f"Datasets: {list(st.session_state.processed_data.keys())}")