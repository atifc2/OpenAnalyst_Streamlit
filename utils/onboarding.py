"""
Onboarding and interactive tour module
Shows first-time users how to use Open Analyst
"""

import streamlit as st

def should_show_onboarding():
    """Check if user should see onboarding (first visit)"""
    # Initialize onboarding state if not present
    if 'onboarding_completed' not in st.session_state:
        st.session_state.onboarding_completed = False
    
    # Initialize onboarding_ready flag to prevent glitch
    if 'onboarding_ready' not in st.session_state:
        st.session_state.onboarding_ready = True
    
    return not st.session_state.onboarding_completed and st.session_state.onboarding_ready

def mark_onboarding_complete():
    """Mark onboarding as completed"""
    st.session_state.onboarding_completed = True

def render_onboarding_modal():
    """Render professional onboarding modal with interactive tour"""
    
    if not should_show_onboarding():
        return
    
    # Professional CSS for onboarding - smooth animations and professional styling
    st.markdown("""
    <style>
    /* Smooth fade-in animation */
    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* Main container animation */
    div[data-testid="stVerticalBlock"] > div:first-child {
        animation: fadeIn 0.5s ease-out;
    }
    
    /* Professional typography */
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        font-weight: 600;
        letter-spacing: -0.5px;
    }
    
    .stMarkdown p {
        line-height: 1.7;
        font-size: 1.05em;
    }
    
    /* Button styling */
    .stButton > button {
        font-weight: 500;
        transition: all 0.3s ease;
        border-radius: 8px;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    /* Progress bar styling */
    .stProgress > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
    }
    
    /* Container spacing */
    div[data-testid="column"] {
        padding: 10px;
    }
    
    /* Ensure smooth rendering */
    .stApp {
        animation: fadeIn 0.3s ease-out;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize tour step
    if 'tour_step' not in st.session_state:
        st.session_state.tour_step = 0
    
    # Tour content - using native Streamlit rendering
    tour_steps = [
        {
            "title": "Welcome to Open Analyst! 📊",
            "type": "welcome",
            "features": [
                {
                    "title": "Your AI-Powered Data Analysis Partner",
                    "description": "Open Analyst transforms complex data into actionable insights using advanced AI. Whether you're analyzing sales, customer feedback, or financial metrics, we make data analysis accessible and powerful."
                },
                {
                    "title": "Let us show you around in just 3 quick steps.",
                    "description": ""
                }
            ]
        },
        {
            "title": "Step 1: Upload Your Data 📁",
            "type": "steps",
            "features": [
                {
                    "icon": "📤",
                    "title": "Upload CSV or Excel Files",
                    "description": "Click the file uploader in the sidebar to get started. You can upload multiple files and switch between them anytime."
                },
                {
                    "icon": "🧹",
                    "title": "Automatic Data Cleaning",
                    "description": "We automatically clean your data by removing empty rows, fixing headers, and handling common issues. No manual preprocessing needed!"
                },
                {
                    "icon": "🎯",
                    "title": "Try Sample Datasets",
                    "description": "Want to explore first? Use our pre-loaded sample datasets: Sales, Survey, and Financial data - all ready to analyze!"
                }
            ]
        },
        {
            "title": "Step 2: Ask Questions 💬",
            "type": "steps",
            "features": [
                {
                    "icon": "🤖",
                    "title": "Conversational AI Analysis",
                    "description": "Simply type your questions in plain English. Ask about trends, patterns, correlations, or request specific visualizations."
                },
                {
                    "icon": "📊",
                    "title": "Smart Visualizations",
                    "description": "Our AI automatically generates charts and graphs to illustrate insights. Bar charts, line graphs, scatter plots - all created for you."
                },
                {
                    "icon": "🔍",
                    "title": "Example Questions",
                    "description": '• "What are the top 5 products by sales?"\n• "Show me customer satisfaction trends over time"\n• "Compare revenue across regions"'
                }
            ]
        },
        {
            "title": "Step 3: Build Your Report 📋",
            "type": "steps",
            "features": [
                {
                    "icon": "📌",
                    "title": "Pin Important Insights",
                    "description": "Found something valuable? Pin it to your canvas! Build a collection of key findings as you explore your data."
                },
                {
                    "icon": "📄",
                    "title": "Export Professional Reports",
                    "description": "When you're done, export your canvas as a professional PDF or interactive HTML report. Perfect for sharing with stakeholders!"
                },
                {
                    "icon": "🔄",
                    "title": "Semantic Search",
                    "description": "Return to previous analyses easily. Our AI remembers your conversations and helps maintain consistent insights across sessions."
                }
            ]
        },
        {
            "title": "You're All Set! 🎉",
            "type": "final",
            "features": [
                {
                    "title": "Ready to start analyzing?",
                    "description": "Here's what to do next:\n\n1. **Upload your data** or **try a sample dataset** from the sidebar\n2. **Ask a question** in the chat to get started\n3. **Pin insights** to build your report as you go"
                },
                {
                    "title": "Pro Tips:",
                    "description": "• Use the search feature to find similar past analyses\n• Download clean data after automatic preprocessing\n• Switch between datasets anytime without losing your work"
                },
                {
                    "title": "Need Help?",
                    "description": "• Type 'help' in chat for guidance\n• Check documentation in the sidebar\n• Demo credentials are available for testing"
                }
            ]
        }
    ]
    
    current_step = tour_steps[st.session_state.tour_step]
    
    # Professional modal container
    with st.container():
        # Title with gradient background
        st.markdown(f"""
        <div style="text-align: center; padding: 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; margin-bottom: 30px;">
            <h1 style="color: white; font-size: 2.5em; margin: 0;">{current_step['title']}</h1>
        </div>
        """, unsafe_allow_html=True)
        
        # Content rendering based on type
        step_type = current_step.get('type', 'welcome')
        
        if step_type == 'welcome':
            # Welcome screen
            for feature in current_step['features']:
                if feature['title']:
                    st.markdown(f"### {feature['title']}")
                if feature['description']:
                    st.markdown(feature['description'])
                st.markdown("")
        
        elif step_type == 'steps':
            # Feature boxes for steps 1, 2, 3
            for feature in current_step['features']:
                with st.container():
                    col1, col2 = st.columns([0.1, 0.9])
                    with col1:
                        st.markdown(f"## {feature['icon']}")
                    with col2:
                        st.markdown(f"**{feature['title']}**")
                        st.markdown(feature['description'])
                st.markdown("")
        
        elif step_type == 'final':
            # Final screen with tips
            for feature in current_step['features']:
                st.markdown(f"### {feature['title']}")
                st.markdown(feature['description'])
                st.markdown("---")
        
        st.divider()
        
        # Navigation
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            if st.session_state.tour_step > 0:
                if st.button("← Previous", use_container_width=True):
                    st.session_state.tour_step -= 1
                    st.rerun()
        
        with col2:
            progress = (st.session_state.tour_step + 1) / len(tour_steps)
            st.progress(progress, text=f"Step {st.session_state.tour_step + 1} of {len(tour_steps)}")
        
        with col3:
            if st.session_state.tour_step < len(tour_steps) - 1:
                if st.button("Next →", use_container_width=True, type="primary"):
                    st.session_state.tour_step += 1
                    st.rerun()
            else:
                if st.button("Get Started! 🚀", use_container_width=True, type="primary"):
                    mark_onboarding_complete()
                    st.session_state.tour_step = 0
                    st.rerun()
        
        # Skip option
        st.markdown("<br>", unsafe_allow_html=True)
        col_skip1, col_skip2, col_skip3 = st.columns([1, 1, 1])
        with col_skip2:
            if st.button("Skip Tour", use_container_width=True):
                mark_onboarding_complete()
                st.session_state.tour_step = 0
                st.rerun()

def add_sample_datasets_section():
    """Add section to load sample datasets"""
    st.sidebar.markdown("---")
    st.sidebar.subheader("📚 Sample Datasets")
    
    sample_files = {
        "🛒 E-commerce Sales": "sample_ecommerce_sales.csv",
        "😊 Customer Survey": "sample_customer_survey.csv",
        "💰 Financial Metrics": "sample_financial_metrics.csv"
    }
    
    for name, filename in sample_files.items():
        if st.sidebar.button(name, use_container_width=True):
            # Load sample dataset
            import pandas as pd
            from utils.data_handler import clean_df, create_derived_columns
            
            try:
                # Initialize processed_data if not exists or is None
                if 'processed_data' not in st.session_state or st.session_state.processed_data is None:
                    st.session_state.processed_data = {}
                
                # Load raw data
                raw_df = pd.read_csv(filename)
                
                # Track original columns
                original_columns = set(raw_df.columns)
                
                # Clean and derive
                cleaned_df, junk_log = clean_df(raw_df.copy())
                
                # Ensure cleaned_df is not None
                if cleaned_df is None:
                    raise ValueError("Data cleaning returned None")
                
                cleaned_df = create_derived_columns(cleaned_df)
                
                # Calculate derived columns
                derived_columns = list(set(cleaned_df.columns) - original_columns)
                
                st.session_state.processed_data[name] = {
                    'df': cleaned_df,
                    'raw_df': raw_df,
                    'junk_log': junk_log,
                    'derived_columns': derived_columns,
                    'profile': None  # Will be generated on demand
                }
                st.session_state.active_dataset_key = name
                
                # Clear messages for fresh start with sample data
                st.session_state.messages = []
                
                st.sidebar.success(f"✅ Loaded {name}")
                st.rerun()
            except FileNotFoundError:
                st.sidebar.error(f"❌ Sample file not found. Please generate samples first.")
            except Exception as e:
                import traceback
                st.sidebar.error(f"❌ Error loading sample: {str(e)}")
                if st.session_state.get('debug_mode', False):
                    st.sidebar.code(traceback.format_exc())
