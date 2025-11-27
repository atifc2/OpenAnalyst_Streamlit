"""
Similar Analyses Widget - Show relevant past analyses
Prominent display of vector DB search results

CRITICAL FIX: Only shows templates that match user's actual columns!
"""

import streamlit as st
import logging
from datetime import datetime
from typing import List, Dict, Optional, Set

logger = logging.getLogger(__name__)


def get_user_columns(df) -> Set[str]:
    """Get normalized column names from user's DataFrame."""
    if df is None:
        return set()
    return set(col.lower().strip() for col in df.columns)


def extract_required_columns_from_template(template_text: str) -> List[str]:
    """
    Extract column names mentioned in template text.
    Templates like "Show revenue by region" mention 'revenue' and 'region'.
    """
    # Common column keywords that might appear in templates
    known_column_patterns = [
        # Time-based
        "hour", "day", "week", "month", "year", "date", "time", "timestamp",
        "day of week", "day_of_week", "dayofweek",
        
        # User/Session
        "user", "users", "unique_users", "session", "sessions", "visitor", "visitors",
        "session duration", "session_duration", "average session", "avg session",
        
        # Content
        "content", "content type", "content_type", "category", "type",
        "video", "vdo", "article", "page", "views",
        
        # Metrics
        "revenue", "sales", "amount", "value", "count", "total",
        "clicks", "impressions", "conversions", "rate", "ratio",
        
        # Dimensions
        "region", "country", "city", "product", "channel", "source", "campaign"
    ]
    
    template_lower = template_text.lower()
    found_columns = []
    
    for pattern in known_column_patterns:
        if pattern in template_lower:
            found_columns.append(pattern.replace(" ", "_"))
    
    return found_columns


def check_column_compatibility(template_text: str, user_columns: Set[str]) -> Dict:
    """
    Check if a template can work with user's columns.
    Returns compatibility info with missing columns.
    """
    # Expanded column synonyms for matching
    COLUMN_SYNONYMS = {
        # Time-based columns
        "hour": ["hour", "hrs", "time_hour", "datetime_hour"],
        "day_of_week": ["day_of_week", "dayofweek", "weekday", "day"],
        "month": ["month", "month_name", "period", "mon"],
        "date": ["date", "datetime", "timestamp", "time", "created", "updated"],
        
        # User/Session columns
        "users": ["users", "user", "unique_users", "unique_user", "visitor", "visitors", "user_count"],
        "session_duration": ["session_duration", "avg_session", "average_session", "duration", "time_spent"],
        "sessions": ["sessions", "session", "visits", "pageviews"],
        
        # Content columns  
        "content_type": ["content_type", "contenttype", "type", "category", "content_category", "format"],
        "content": ["content", "article", "page", "post", "video", "vdo", "media"],
        
        # Metrics
        "revenue": ["revenue", "sales", "total_sale", "amount", "value", "income", "turnover", "lns_content"],
        "views": ["views", "pageviews", "impressions", "vdo", "watch"],
        "count": ["count", "total", "sum", "qty", "quantity"],
        
        # Other
        "region": ["region", "area", "territory", "location", "country", "state", "city"],
        "product": ["product", "item", "sku", "product_name", "goods"],
        "category": ["category", "type", "class", "group", "segment"],
    }
    
    required_cols = extract_required_columns_from_template(template_text)
    
    missing_cols = []
    matched_cols = []
    
    for req_col in required_cols:
        # Check if user has this column or a synonym
        found = False
        
        # Direct match
        if req_col in user_columns:
            matched_cols.append(req_col)
            found = True
            continue
        
        # Check synonyms
        synonyms = COLUMN_SYNONYMS.get(req_col, [req_col])
        for synonym in synonyms:
            if synonym in user_columns:
                matched_cols.append(f"{req_col}→{synonym}")
                found = True
                break
            # Partial match
            for user_col in user_columns:
                if synonym in user_col or user_col in synonym:
                    matched_cols.append(f"{req_col}→{user_col}")
                    found = True
                    break
            if found:
                break
        
        if not found:
            missing_cols.append(req_col)
    
    is_compatible = len(missing_cols) == 0 or len(required_cols) == 0
    
    return {
        "is_compatible": is_compatible,
        "required_columns": required_cols,
        "matched_columns": matched_cols,
        "missing_columns": missing_cols,
        "match_score": len(matched_cols) / max(len(required_cols), 1)
    }


def render_similar_analyses_widget(vector_store, current_domain, current_dataset_name, user_id=None):
    """
    Render HYBRID MODEL widget showing community + personal analyses.
    
    CRITICAL: Now validates templates against user's actual columns!
    Only shows templates that can work with user's data.
    
    Args:
        vector_store: VectorStore instance
        current_domain: Detected domain of current data (1 of 8 domains)
        current_dataset_name: Name of active dataset
        user_id: Current user ID for personal workspace filtering
    """
    
    if not vector_store or not vector_store.client:
        return
    
    # Get user's actual columns
    user_columns = set()
    if st.session_state.get('processed_data') and st.session_state.get('active_dataset_key'):
        active_df = st.session_state.processed_data.get(st.session_state.active_dataset_key, {}).get('df')
        if active_df is not None:
            user_columns = get_user_columns(active_df)
    
    # Get domain emoji and color FIRST
    from utils.domain_detector import get_domain_emoji, get_domain_color
    
    domain_emoji = get_domain_emoji(current_domain)
    domain_color = get_domain_color(current_domain)
    
    # PROMINENT DOMAIN MODE INDICATOR - Show this BIG and CLEAR!
    st.markdown(
        f"""
        <div style='
            padding: 16px 20px;
            border-radius: 8px;
            background: linear-gradient(135deg, {domain_color}30 0%, {domain_color}10 100%);
            border: 2px solid {domain_color};
            margin-bottom: 20px;
            text-align: center;
        '>
            <div style='font-size: 2em; margin-bottom: 5px;'>{domain_emoji}</div>
            <div style='font-size: 1.2em; font-weight: 700; color: {domain_color};'>
                {current_domain.upper()} ANALYST MODE
            </div>
            <div style='font-size: 0.85em; color: #666; margin-top: 5px;'>
                Showing {current_domain.title()}-specific templates
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    with st.container():
        st.markdown("### 💡 Quick Actions")
        
        # Show user's available columns
        if user_columns:
            with st.expander("📋 Your Data Columns", expanded=False):
                cols_display = ", ".join(sorted(user_columns)[:15])
                if len(user_columns) > 15:
                    cols_display += f"... (+{len(user_columns) - 15} more)"
                st.caption(f"Available: {cols_display}")
        
        st.caption("📚 From Community (Matched to Your Data)")
        
        try:
            # ==================== SMART TEMPLATE MATCHING ====================
            logger.info(f"Searching community templates for domain: {current_domain}")
            
            try:
                community_analyses = vector_store.search_by_tier(
                    query_text=f"analyze {current_domain} data",
                    tier="public",
                    domain=current_domain,
                    limit=10,  # Get more to filter
                    min_score=0.5
                )
            except Exception as search_err:
                logger.error(f"search_by_tier failed: {search_err}")
                community_analyses = []
            
            # DEFENSIVE: Ensure it's a list of dicts
            if not isinstance(community_analyses, list):
                logger.warning(f"search_by_tier returned non-list: {type(community_analyses)}")
                community_analyses = []
            
            # FILTER templates by column compatibility!
            compatible_analyses = []
            incompatible_count = 0
            
            for item in community_analyses:
                if not isinstance(item, dict) or 'content' not in item:
                    continue
                    
                content = str(item.get('content', ''))
                
                # Check compatibility with user's columns
                compat = check_column_compatibility(content, user_columns)
                
                if compat["is_compatible"] or compat["match_score"] >= 0.5:
                    item["_compatibility"] = compat
                    compatible_analyses.append(item)
                else:
                    incompatible_count += 1
                    logger.debug(f"Template incompatible - missing: {compat['missing_columns']}")
            
            # Show only top 3 compatible templates
            compatible_analyses = compatible_analyses[:3]
            
            logger.info(f"Found {len(compatible_analyses)} compatible analyses (filtered out {incompatible_count})")
            
            if compatible_analyses:
                for i, analysis in enumerate(compatible_analyses, 1):
                    try:
                        content = str(analysis.get('content', ''))[:100]
                        button_key = f"community_{current_domain}_{i}"
                        
                        # Emoji for different query types
                        type_emoji = {
                            "aggregation": "📊",
                            "trend_analysis": "📈",
                            "comparison": "⚖️",
                            "analysis": "🔍"
                        }.get(analysis.get('query_type', 'analysis'), "💬")
                        
                        query_type = analysis.get('query_type', 'analysis')
                        query_type_display = query_type.replace('_', ' ').title() if isinstance(query_type, str) else 'Analysis'
                        
                        if st.button(
                            f"{type_emoji} {content}", 
                            key=button_key, 
                            use_container_width=True,
                            help=f"✓ Matches your columns • {query_type_display}"
                        ):
                            st.session_state.messages.append({
                                "role": "user",
                                "content": analysis.get('content', content)
                            })
                            st.rerun()
                    except Exception as btn_err:
                        logger.error(f"Button {i} error: {btn_err}")
                        continue
            
            # ==================== SMART FALLBACK: DATA-AWARE QUESTIONS ====================
            if not compatible_analyses:
                st.info(f"💡 Generating suggestions based on YOUR columns...")
                
                # Generate questions based on ACTUAL user columns
                starter_questions = generate_smart_questions(user_columns, current_domain)
                
                for i, question in enumerate(starter_questions[:3], 1):
                    button_key = f"smart_{current_domain}_{i}"
                    if st.button(f"💬 {question}", key=button_key, use_container_width=True):
                        st.session_state.messages.append({
                            "role": "user",
                            "content": question
                        })
                        st.rerun()
            
            # Show info about filtered templates
            if incompatible_count > 0:
                st.caption(f"ℹ️ {incompatible_count} templates hidden (missing columns)")
        
        except Exception as e:
            logger.error(f"Error rendering similar analyses: {e}")
            st.warning("⚠️ Recommended analyses temporarily unavailable")
        
        st.divider()


def generate_smart_questions(user_columns: Set[str], domain: str) -> List[str]:
    """
    Generate smart questions based on user's actual columns.
    This ensures questions are always answerable!
    """
    questions = []
    cols = list(user_columns)
    
    # Find numeric-looking columns
    numeric_hints = ["count", "total", "sum", "amount", "value", "revenue", "sales", "users", "views", "rate", "score"]
    category_hints = ["type", "category", "region", "country", "product", "name", "channel", "source", "segment"]
    time_hints = ["date", "time", "month", "year", "day", "hour", "week", "timestamp"]
    
    numeric_cols = [c for c in cols if any(h in c for h in numeric_hints)]
    category_cols = [c for c in cols if any(h in c for h in category_hints)]
    time_cols = [c for c in cols if any(h in c for h in time_hints)]
    
    # Generate relevant questions
    if numeric_cols:
        questions.append(f"What is the total {numeric_cols[0]}?")
        if len(numeric_cols) > 1:
            questions.append(f"Compare {numeric_cols[0]} vs {numeric_cols[1]}")
    
    if category_cols and numeric_cols:
        questions.append(f"Show {numeric_cols[0]} by {category_cols[0]}")
    
    if time_cols and numeric_cols:
        questions.append(f"Show {numeric_cols[0]} trend over {time_cols[0]}")
    
    if category_cols:
        questions.append(f"What are the top 10 {category_cols[0]}s?")
    
    # Domain-specific fallbacks
    domain_questions = {
        "sales": ["Show total revenue", "Top selling products", "Sales by region"],
        "marketing": ["Campaign performance", "Conversion rates", "Cost per acquisition"],
        "hr": ["Employee count by department", "Average tenure", "Turnover rate"],
        "financial": ["Budget vs actual", "Profit margin", "Expense breakdown"],
        "survey": ["Average satisfaction score", "Response distribution", "Feedback themes"],
        "product": ["Feature usage", "User retention", "Adoption rates"],
        "business": ["Key metrics summary", "Performance vs targets", "Growth trends"],
        "operations": ["Process efficiency", "Cycle times", "Quality metrics"],
        "general": ["Summary of data", "Key trends", "Distribution analysis"]
    }
    
    if not questions:
        questions = domain_questions.get(domain, domain_questions["general"])
    
    return questions[:5]


def render_domain_indicator(domain, confidence):
    """
    Render a small badge showing detected domain.
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
