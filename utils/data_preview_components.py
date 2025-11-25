"""
Data preview and quality visualization components
"""

import streamlit as st
import pandas as pd
from utils.data_quality import (
    calculate_data_quality_score,
    get_cleaning_stats,
    format_memory_size,
    get_star_rating,
    identify_derived_columns
)

def render_data_quality_dashboard(raw_df, cleaned_df, derived_columns=None):
    """
    Render comprehensive data quality dashboard with before/after comparison
    """
    if derived_columns is None:
        derived_columns = []
    
    # Calculate quality score and stats
    quality_data = calculate_data_quality_score(raw_df, cleaned_df, derived_columns)
    cleaning_stats = get_cleaning_stats(raw_df, cleaned_df)
    
    # Overall metrics at the top
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Rows",
            f"{cleaning_stats['rows']['after']:,}",
            delta=f"{cleaning_stats['rows']['change']:,}" if cleaning_stats['rows']['change'] != 0 else None
        )
    
    with col2:
        st.metric(
            "Columns",
            cleaning_stats['columns']['after'],
            delta=f"+{cleaning_stats['columns']['change']}" if cleaning_stats['columns']['change'] > 0 else None
        )
    
    with col3:
        st.metric(
            "Missing Values",
            f"{cleaning_stats['missing']['after']:,}",
            delta=f"{cleaning_stats['missing']['change']:,}" if cleaning_stats['missing']['change'] != 0 else None,
            delta_color="inverse"  # Lower is better
        )
    
    with col4:
        st.metric(
            "Memory",
            cleaning_stats['memory']['after_formatted'].split('(')[0].strip(),
            delta=f"{cleaning_stats['memory']['change_pct']:.1f}%"  if cleaning_stats['memory']['change'] != 0 else None
        )
    
    st.markdown("---")
    
    # Data Quality Score
    score = quality_data['overall_score']
    stars = get_star_rating(score)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(f"### 📊 Data Quality: {score}/100 {stars}")
        
        # Progress bar for visual appeal
        st.progress(score / 100)
    
    with col2:
        if st.button("📊 View Cleaning Impact", use_container_width=True):
            st.session_state.show_cleaning_impact = True
        
        if st.button("ℹ️ How is this calculated?", use_container_width=True):
            st.session_state.show_quality_breakdown = True
    
    # Show derived columns if any
    if derived_columns:
        with st.expander(f"✨ Auto-Generated Columns ({len(derived_columns)})", expanded=False):
            st.markdown("**These columns were automatically created to enhance your analysis:**")
            st.markdown("")
            
            for col in derived_columns:
                if 'total' in col.lower() or 'sale' in col.lower():
                    st.markdown(f"• **{col}** - Calculated from quantity × price")
                elif 'month' in col.lower():
                    st.markdown(f"• **{col}** - Extracted from date column")
                elif 'year' in col.lower():
                    st.markdown(f"• **{col}** - Extracted from date column")
                elif 'day' in col.lower():
                    st.markdown(f"• **{col}** - Extracted from date column")
                else:
                    st.markdown(f"• **{col}** - Auto-generated")
            
            if st.button("🔍 Show Detailed Derivation Logic"):
                st.session_state.show_derivation_modal = True

@st.dialog("🧹 Cleaning Impact Report", width="large")
def show_cleaning_impact_modal(raw_df, cleaned_df, cleaning_stats):
    """Modal showing detailed before/after comparison"""
    
    st.markdown("### Before Cleaning  →  After Cleaning")
    st.markdown("---")
    
    # Create comparison table
    comparison_data = {
        "Metric": ["Rows", "Columns", "Missing Values", "Duplicate Rows", "Memory"],
        "Before": [
            f"{cleaning_stats['rows']['before']:,}",
            str(cleaning_stats['columns']['before']),
            f"{cleaning_stats['missing']['before']:,}",
            f"{cleaning_stats['duplicates']['before']:,}",
            cleaning_stats['memory']['before_formatted']
        ],
        "After": [
            f"{cleaning_stats['rows']['after']:,}",
            str(cleaning_stats['columns']['after']),
            f"{cleaning_stats['missing']['after']:,}",
            f"{cleaning_stats['duplicates']['after']:,}",
            cleaning_stats['memory']['after_formatted']
        ],
        "Impact": [
            f"{cleaning_stats['rows']['change']:+,} ({cleaning_stats['rows']['change_pct']:+.1f}%)",
            f"{cleaning_stats['columns']['change']:+}",
            f"{cleaning_stats['missing']['change']:+,} ✅",
            f"{cleaning_stats['duplicates']['change']:+,} ✅",
            f"{cleaning_stats['memory']['change_pct']:+.1f}%"
        ]
    }
    
    comparison_df = pd.DataFrame(comparison_data)
    st.dataframe(comparison_df, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # Buttons to view raw/cleaned data
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 View Raw Data Table", use_container_width=True):
            st.session_state.show_raw_table = True
    
    with col2:
        if st.button("✨ View Cleaned Data Table", use_container_width=True):
            st.session_state.show_cleaned_table = True

@st.dialog("📊 Data Quality Score Breakdown", width="large")
def show_quality_breakdown_modal(quality_data):
    """Modal showing detailed quality score calculation"""
    
    st.markdown(f"### Your Score: {quality_data['overall_score']}/100 {get_star_rating(quality_data['overall_score'])}")
    st.markdown("---")
    
    st.markdown("### Component Scores")
    st.markdown("")
    
    components = quality_data['components']
    
    for comp_name, comp_data in components.items():
        with st.expander(f"**{comp_name.title()}**: {comp_data['score']}/100 ({comp_data['weight']}% weight)", expanded=False):
            st.progress(comp_data['score'] / 100)
            
            st.markdown("**Details:**")
            for key, value in comp_data['details'].items():
                formatted_key = key.replace('_', ' ').title()
                st.markdown(f"- {formatted_key}: {value:,}" if isinstance(value, int) else f"- {formatted_key}: {value}")
    
    # Show enrichment bonus
    if quality_data['enrichment_bonus'] > 0:
        st.markdown("---")
        st.success(f"**📈 Enrichment Bonus: +{quality_data['enrichment_bonus']} points**")
        st.markdown(f"Added {quality_data['derived_columns_count']} derived columns to enhance analysis capabilities")
    
    st.markdown("---")
    
    # Scoring formula
    with st.expander("🔢 How is the score calculated?"):
        st.code("""
quality_score = (
    completeness × 0.30 +    # 30% weight
    uniqueness × 0.25 +      # 25% weight  
    validity × 0.25 +        # 25% weight
    consistency × 0.20       # 20% weight
) + enrichment_bonus
        """, language="python")
        
        st.markdown("""
        **Scoring Components:**
        - **Completeness**: Measures how much missing data was filled
        - **Uniqueness**: Measures duplicate row removal
        - **Validity**: Checks for outliers and data quality issues
        - **Consistency**: Validates naming conventions and formatting
        - **Enrichment**: Bonus points for derived columns that add value
        """)

@st.dialog("✨ Column Derivation Logic", width="large")
def show_derivation_logic_modal(raw_df, cleaned_df, derived_columns):
    """Modal showing how each derived column was created"""
    
    st.markdown("### Auto-Generated Column Logic")
    st.markdown("We detected patterns in your data and created helpful columns to accelerate your analysis.")
    st.markdown("---")
    
    for col in derived_columns:
        st.markdown(f"#### {col}")
        
        # Determine derivation logic
        if 'total' in col.lower() or 'sale' in col.lower():
            st.markdown("**Why we added this:**")
            st.markdown("• Found numeric 'quantity' and 'price' columns")
            st.markdown("• Multiplication suggests transactional data")
            st.markdown("• Enables revenue analysis without manual calculation")
            
            # Show example
            if 'quantity' in cleaned_df.columns and 'price' in cleaned_df.columns:
                st.code(f"{col} = quantity × price", language="python")
                
                if len(cleaned_df) > 0:
                    example_row = cleaned_df.iloc[0]
                    st.markdown(f"**Example (Row 1):**")
                    st.markdown(f"quantity: {example_row.get('quantity', 'N/A')} × price: ${example_row.get('price', 'N/A')} = {col}: ${example_row.get(col, 'N/A')}")
        
        elif 'month' in col.lower() or 'year' in col.lower() or 'day' in col.lower():
            st.markdown("**Why we added this:**")
            st.markdown("• Found date column in your data")
            st.markdown("• Enables time-series analysis")
            st.markdown("• Supports trend detection and seasonality")
            
            # Find source date column
            date_cols = [c for c in raw_df.columns if 'date' in c.lower()]
            if date_cols:
                source_col = date_cols[0]
                st.code(f"{col} = extract from {source_col}", language="python")
                
                if len(cleaned_df) > 0:
                    example_row = cleaned_df.iloc[0]
                    st.markdown(f"**Example (Row 1):**")
                    st.markdown(f"{source_col}: {example_row.get(source_col, 'N/A')} → {col}: {example_row.get(col, 'N/A')}")
        
        st.markdown("---")
    
    st.markdown("### 💡 You can use these columns in your queries:")
    st.markdown("• *\"Show sales trends by month\"*")
    st.markdown("• *\"Compare weekday vs weekend performance\"*")
    st.markdown("• *\"Analyze total revenue by category\"*")

@st.dialog("📥 Raw Data", width="large")
def show_raw_data_modal(raw_df):
    """Modal showing raw uploaded data"""
    st.markdown("### Raw Uploaded Data")
    st.caption("⚠️ This is your original data before AI processing")
    st.markdown("---")
    
    st.dataframe(raw_df, use_container_width=True, height=500)
    
    st.markdown(f"**Shape:** {raw_df.shape[0]:,} rows × {raw_df.shape[1]} columns")
    st.markdown(f"**Memory:** {format_memory_size(raw_df.memory_usage(deep=True).sum())}")

@st.dialog("✨ Cleaned Data", width="large")
def show_cleaned_data_modal(cleaned_df):
    """Modal showing cleaned processed data"""
    st.markdown("### AI-Ready Cleaned Data")
    st.caption("✅ This is the data used for your analysis")
    st.markdown("---")
    
    st.dataframe(cleaned_df, use_container_width=True, height=500)
    
    st.markdown(f"**Shape:** {cleaned_df.shape[0]:,} rows × {cleaned_df.shape[1]} columns")
    st.markdown(f"**Memory:** {format_memory_size(cleaned_df.memory_usage(deep=True).sum())}")
