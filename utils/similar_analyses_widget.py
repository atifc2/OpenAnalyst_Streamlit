"""
Similar Analyses Widget - Show relevant past analyses
Prominent display of vector DB search results
"""

import streamlit as st
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def render_similar_analyses_widget(vector_store, current_domain, current_dataset_name):
    """
    Render prominent widget showing similar past analyses.
    Appears at top of sidebar before AI Stats.
    
    Args:
        vector_store: VectorStore instance
        current_domain: Detected domain of current data
        current_dataset_name: Name of active dataset
    """
    
    if not vector_store or not vector_store.client:
        return
    
    with st.container():
        st.markdown("### 🔍 Similar Past Analyses")
        st.caption("Learn from analyses done on similar data")
        
        # Get domain emoji and color
        from utils.domain_detector import get_domain_emoji, get_domain_color
        
        domain_emoji = get_domain_emoji(current_domain)
        domain_color = get_domain_color(current_domain)
        
        # Show current domain
        st.markdown(
            f"""
            <div style='padding: 8px; border-radius: 5px; background-color: {domain_color}20; border-left: 3px solid {domain_color};'>
                {domain_emoji} <b>{current_domain.title()} Data Detected</b>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Search for similar analyses in this domain
        try:
            # Generic query to find all analyses in this domain
            similar = vector_store.search_by_domain(
                query_text=f"analyze {current_domain} data",
                domain=current_domain,
                limit=5,
                min_score=0.5  # Lower threshold to show more results
            )
            
            if similar:
                st.markdown(f"**Found {len(similar)} relevant analyses:**")
                
                for i, analysis in enumerate(similar, 1):
                    score_pct = int(analysis['score'] * 100)
                    
                    # Star rating based on score
                    if score_pct >= 90:
                        stars = "⭐⭐⭐⭐⭐"
                    elif score_pct >= 80:
                        stars = "⭐⭐⭐⭐"
                    elif score_pct >= 70:
                        stars = "⭐⭐⭐"
                    else:
                        stars = "⭐⭐"
                    
                    with st.expander(f"#{i}: {analysis['content'][:50]}...", expanded=i==1):
                        st.markdown(f"**Question:** {analysis['content']}")
                        st.markdown(f"**Relevance:** {stars} ({score_pct}% match)")
                        st.markdown(f"**Type:** {analysis.get('query_type', 'analysis').replace('_', ' ').title()}")
                        
                        # "Run on Your Data" button
                        button_key = f"run_similar_{i}_{hash(analysis['content'])}"
                        if st.button("▶️ Run on Your Data", key=button_key, use_container_width=True, type="primary"):
                            # Add this question to chat
                            st.session_state.messages.append({
                                "role": "user",
                                "content": analysis['content']
                            })
                            st.rerun()
                        
                        st.caption(f"From: {analysis.get('dataset', 'Example')} | {analysis.get('timestamp', '')[:10]}")
            
            else:
                st.info(f"💡 No similar {current_domain} analyses yet. Be the first!")
                
                # Show generic examples as fallback
                st.markdown("**Try these starter questions:**")
                
                STARTER_QUESTIONS = {
                    "sales": [
                        "Show revenue by region",
                        "What are the top 10 products?",
                        "Analyze monthly sales trends"
                    ],
                    "marketing": [
                        "Which campaigns have best ROI?",
                        "Show conversion funnel",
                        "Analyze cost per acquisition"
                    ],
                    "hr": [
                        "Show headcount by department",
                        "What's average employee tenure?",
                        "Analyze turnover rates"
                    ],
                    "financial": [
                        "Show budget vs actual variance",
                        "What's our profit margin trend?",
                        "Analyze expenses by category"
                    ],
                    "survey": [
                        "What's the average satisfaction score?",
                        "Show NPS distribution",
                        "Analyze sentiment trends"
                    ],
                    "general": [
                        "Show me a summary of the data",
                        "What are the key trends?",
                        "Identify any outliers"
                    ]
                }
                
                questions = STARTER_QUESTIONS.get(current_domain, STARTER_QUESTIONS["general"])
                
                for i, question in enumerate(questions, 1):
                    button_key = f"starter_{i}_{hash(question)}"
                    if st.button(f"💬 {question}", key=button_key, use_container_width=True):
                        st.session_state.messages.append({
                            "role": "user",
                            "content": question
                        })
                        st.rerun()
        
        except Exception as e:
            logger.error(f"Error rendering similar analyses: {e}")
            st.warning("⚠️ Similar analyses feature temporarily unavailable")
        
        st.divider()


def render_domain_indicator(domain, confidence):
    """
    Render a small badge showing detected domain.
    Can be placed anywhere in the UI.
    
    Args:
        domain: Detected domain name
        confidence: Confidence score (0-1)
    """
    from utils.domain_detector import get_domain_emoji, get_domain_color
    
    emoji = get_domain_emoji(domain)
    color = get_domain_color(domain)
    confidence_pct = int(confidence * 100)
    
    st.markdown(
        f"""
        <div style='
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            background-color: {color}30;
            border: 1px solid {color};
            font-size: 0.85em;
            font-weight: 500;
        '>
            {emoji} {domain.title()} Mode ({confidence_pct}% confident)
        </div>
        """,
        unsafe_allow_html=True
    )
