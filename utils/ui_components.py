import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import uuid
import datetime

def render_plotly_chart(chart_data, df):
    """
    Renders a Plotly chart based on AI-generated chart_data.
    Handles: bar, pie, line, scatter charts with defensive error handling.
    """
    try:
        # Debug logging
        with st.expander("🔍 Debug: Chart Data Details"):
            st.write("Chart Data:", chart_data)
            st.write("DataFrame Columns:", df.columns.tolist())
        
        title = chart_data.get("title", "AI Generated Chart")
        chart_type = chart_data.get("chart_type", "").lower()

        # Check if we have pre-aggregated data
        if chart_data.get("data"):
            import pandas as pd
            df = pd.DataFrame(chart_data["data"])
            st.write("Using pre-aggregated data:", df)

        # Defensive check for column existence
        required_cols = []
        if chart_type in ["bar", "line", "scatter"]:
            x_col = chart_data.get("x_column")
            y_col = chart_data.get("y_column")
            if x_col:
                required_cols.append(x_col)
            if y_col:
                required_cols.append(y_col)
        elif chart_type == "pie":
            color_col = chart_data.get("color_column")
            if color_col:
                required_cols.append(color_col)
        
        # Check if all required columns exist
        missing_cols = [col for col in required_cols if col and col not in df.columns]
        if missing_cols:
            st.error(f"❌ Chart Error: Column(s) not found: {', '.join(missing_cols)}")
            st.info(f"Available columns: {', '.join(df.columns.tolist())}")
            return

        # Render the appropriate chart type
        if chart_type == "pie":
            names_col = chart_data["color_column"]
            # Check for too many unique values
            if df[names_col].nunique() > 20:
                st.warning(f"⚠️ Skipping pie chart: '{names_col}' has {df[names_col].nunique()} unique values (max 20)")
                return
            # Create value counts for pie chart
            value_counts = df[names_col].value_counts().reset_index()
            value_counts.columns = [names_col, 'count']
            fig = px.pie(
                value_counts, 
                names=names_col, 
                values='count', 
                title=title,
                hole=0.3  # Makes it a donut chart - looks more modern
            )
        elif chart_type == "bar":
            x_col = chart_data.get("x_column")
            y_col = chart_data.get("y_column")
            color_col = chart_data.get("color_column")
            # Handle case where we need to aggregate data
            if df[x_col].nunique() < len(df):
                # Aggregate if there are duplicate x values
                agg_df = df.groupby(x_col)[y_col].sum().reset_index()
                fig = px.bar(agg_df, x=x_col, y=y_col, title=title)
            else:
                fig = px.bar(df, x=x_col, y=y_col, color=color_col, title=title)
        elif chart_type == "line":
            x_col = chart_data.get("x_column")
            y_col = chart_data.get("y_column")
            color_col = chart_data.get("color_column")
            fig = px.line(df, x=x_col, y=y_col, color=color_col, title=title)
        elif chart_type == "scatter":
            x_col = chart_data.get("x_column")
            y_col = chart_data.get("y_column")
            color_col = chart_data.get("color_column")
            fig = px.scatter(df, x=x_col, y=y_col, color=color_col, title=title)
        elif chart_type == "histogram":
            x_col = chart_data.get("x_column")
            color_col = chart_data.get("color_column")
            fig = px.histogram(df, x=x_col, color=color_col, title=title)
        elif chart_type == "box":
            x_col = chart_data.get("x_column")
            y_col = chart_data.get("y_column")
            fig = px.box(df, x=x_col, y=y_col, title=title)
        elif chart_type == "area":
            x_col = chart_data.get("x_column")
            y_col = chart_data.get("y_column")
            fig = px.area(df, x=x_col, y=y_col, title=title)
        elif chart_type == "density_heatmap":
            x_col = chart_data.get("x_column")
            y_col = chart_data.get("y_column")
            fig = px.density_heatmap(df, x=x_col, y=y_col, title=title)
        elif chart_type == "density_contour":
            x_col = chart_data.get("x_column")
            y_col = chart_data.get("y_column")
            fig = px.density_contour(df, x=x_col, y=y_col, title=title)
        else:
            st.warning(f"⚠️ Unsupported chart type: '{chart_type}'")
            st.info("Supported types: bar, pie, line, scatter, histogram, box, area, density_heatmap, density_contour")
            return
        
        # Update layout for better appearance
        fig.update_layout(
            template="plotly_white",
            hovermode='closest',
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except KeyError as ke:
        st.error(f"❌ Chart Error: Missing required field in chart_data: {ke}")
        st.json(chart_data)
    except Exception as e:
        st.error(f"❌ Failed to render chart '{title}'")
        st.error(f"Error: {str(e)}")
        st.json(chart_data)
        import traceback
        with st.expander("🔍 Full Error Details"):
            st.code(traceback.format_exc())

def render_chat_response(ai_response, active_df, msg_key):
    """Enhanced response rendering with results-first display and reasoning toggle"""
    
    if isinstance(ai_response, dict):
        content = ai_response.get("content", "")
        reasoning = ai_response.get("reasoning", "")
        
        # 🧠 RAG INDICATOR - Show if AI used past context
        if ai_response.get('_rag_context_used'):
            st.markdown("""
            <div style='
                padding: 8px 12px;
                margin-bottom: 12px;
                border-radius: 6px;
                background: linear-gradient(135deg, rgba(139, 92, 246, 0.15) 0%, rgba(59, 130, 246, 0.15) 100%);
                border-left: 3px solid #8B5CF6;
                font-size: 13px;
            '>
                🧠 <strong>AI Memory Active</strong> — Using insights from your previous questions to provide better analysis
            </div>
            """, unsafe_allow_html=True)
        
        # Display main content (results)
        st.markdown(content)
        
        # Collapsible reasoning section (hidden by default)
        if reasoning:
            with st.expander("🔍 Show Reasoning", expanded=False):
                st.markdown(f"**Technical Details:**\n\n{reasoning}")
        
        # Create chart if visualizable
        chart_data = None
        chart_created = False
        
        if ai_response.get("is_visualizable") and ai_response.get("chart_data"):
            chart_data = ai_response["chart_data"]
            
            # Validate columns exist
            x_col = chart_data.get("x_column")
            y_col = chart_data.get("y_column")
            color_col = chart_data.get("color_column")
            
            required_cols = [col for col in [x_col, y_col, color_col] if col]
            missing_cols = [col for col in required_cols if col and col not in active_df.columns]
            
            if missing_cols:
                # DON'T show error - just log it and skip chart (text answer is still good!)
                import logging
                logging.getLogger(__name__).debug(f"Chart skipped - columns not found: {missing_cols}")
                # Show a subtle info instead of scary red error
                with st.expander("ℹ️ Chart not available", expanded=False):
                    st.caption(f"Missing columns: {', '.join(missing_cols)}")
                    st.caption(f"Available: {', '.join(active_df.columns[:10])}...")
            else:
                # Create chart with type selection
                chart_created = create_chart(chart_data, active_df, msg_key, allow_chart_selection=True)
        
        # Button row
        col1, col2 = st.columns(2)
        
        with col1:
            # Add to Canvas button - ALWAYS show
            pin_key = f"pin_canvas_{msg_key}_{hash(str(content) + str(chart_data))}"
            if st.button(f"📌 Add to Canvas", key=pin_key, type="secondary"):
                add_to_canvas(content, chart_data, active_df)
                st.success("✅ Added to canvas!")
                st.rerun()
        
        with col2:
            # Generate Chart button - show if AI suggests it OR if no chart but mentions data relationships
            show_generate_chart = False
            
            if not chart_created:  # Only show if no chart was already created
                # Check if AI provided chart suggestion
                if ai_response.get("generate_chart_suggestion"):
                    show_generate_chart = True
                else:
                    # Smart detection - look for data relationship keywords in the content
                    chart_keywords = [
                        'trend', 'distribution', 'comparison', 'over time', 'by category',
                        'highest', 'lowest', 'increase', 'decrease', 'sales from', 'performance',
                        'across', 'between', 'among', 'top', 'bottom', 'most', 'least'
                    ]
                    if any(keyword in content.lower() for keyword in chart_keywords):
                        show_generate_chart = True
            
            if show_generate_chart:
                chart_gen_key = f"gen_chart_{msg_key}_{hash(content)}"
                if st.button("📊 Generate Chart from Insight", key=chart_gen_key, type="primary"):
                    generate_chart_from_insight(content, active_df, msg_key)
                    st.rerun()
        
        # Show suggested actions as clickable buttons
        if ai_response.get("suggested_actions"):
            st.markdown("**💡 Suggested next steps:**")
            
            num_actions = len(ai_response["suggested_actions"])
            if num_actions <= 3:
                cols = st.columns(num_actions)
            else:
                cols = st.columns(3)
            
            for i, action in enumerate(ai_response["suggested_actions"]):
                col_index = i % len(cols)
                with cols[col_index]:
                    action_key = f"action_{msg_key}_{i}_{hash(action)}"
                    if st.button(action, key=action_key, use_container_width=True):
                        st.session_state.messages.append({"role": "user", "content": action})
                        st.rerun()
    else:
        # Handle simple text responses
        st.markdown(str(ai_response))
        
        # Add to Canvas button for simple text
        simple_pin_key = f"pin_simple_{msg_key}_{hash(str(ai_response))}"
        if st.button(f"📌 Add to Canvas", key=simple_pin_key, type="secondary"):
            add_to_canvas(str(ai_response), None, active_df)
            st.success("✅ Added to canvas!")
            st.rerun()

def generate_chart_from_insight(insight_text, active_df, msg_key):
    """Generate chart based on AI insight using another AI call"""
    
    # Create a focused prompt for chart generation
    chart_prompt = f"""
    Based on this insight: "{insight_text}"
    
    Create a chart that best visualizes this analysis using the available data.
    Focus on creating a specific, actionable visualization.
    """
    
    # Add as a new message to trigger AI response
    st.session_state.messages.append({
        "role": "user", 
        "content": f"Create a visualization for this insight: {insight_text}"
    })

def add_to_canvas(text_content, chart_data, active_df):
    """Add response to canvas with duplicate prevention"""
    # Determine title
    if chart_data:
        title = chart_data.get("title", "Analysis with Chart")
    else:
        # Use first 50 chars of text as title
        title = text_content[:50] + "..." if len(text_content) > 50 else text_content
    
    # Generate unique hash for duplicate detection
    import hashlib
    content_hash = hashlib.md5(
        f"{text_content}{str(chart_data)}".encode()
    ).hexdigest()
    
    # Check for duplicates
    if "canvas_items" not in st.session_state:
        st.session_state.canvas_items = []
    
    # Check if this exact item already exists
    for existing_item in st.session_state.canvas_items:
        existing_hash = existing_item.get("content_hash", "")
        if existing_hash == content_hash:
            st.warning("⚠️ This item is already in your canvas!")
            return
    
    # Create canvas item
    canvas_item = {
        "title": title,
        "text_content": text_content,
        "chart_data": chart_data,
        "content_hash": content_hash,  # Store hash for duplicate detection
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "pinned_at": datetime.datetime.now().strftime("%H:%M:%S"),
        "dataset_source": st.session_state.get("active_dataset_key", "Unknown")
    }
    
    st.session_state.canvas_items.append(canvas_item)

def render_canvas_item(item, df, index):
    """Render canvas item with improved text visibility"""
    # Add custom CSS for better text wrapping and visibility
    st.markdown("""
        <style>
        .canvas-item-container {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 15px;
            border-left: 4px solid #4CAF50;
        }
        .canvas-item-content {
            word-wrap: break-word;
            white-space: pre-wrap;
            line-height: 1.6;
            max-width: 100%;
            overflow-wrap: break-word;
        }
        </style>
    """, unsafe_allow_html=True)
    
    with st.container():
        # Header
        col1, col2, col3 = st.columns([4, 1, 1])
        
        with col1:
            title = item.get("title", f"Canvas Item {index + 1}")
            st.markdown(f"**📌 {title}**")
        
        with col2:
            st.caption(f"📅 {item.get('pinned_at', 'Unknown')}")
            st.caption(f"📊 {item.get('dataset_source', 'Unknown')}")
        
        with col3:
            if st.button("🗑️", key=f"remove_{index}", help="Remove from canvas"):
                if "canvas_items" in st.session_state:
                    st.session_state.canvas_items.pop(index)
                    st.rerun()
        
        # Show text content with improved styling
        text_content = item.get("text_content", "")
        if text_content:
            st.markdown(f'<div class="canvas-item-content">{text_content}</div>', unsafe_allow_html=True)
        
        # Show chart if available
        chart_data = item.get("chart_data")
        if chart_data and df is not None:
            try:
                # Check if columns exist
                x_col = chart_data.get("x_column")
                y_col = chart_data.get("y_column")
                color_col = chart_data.get("color_column")
                
                required_cols = [col for col in [x_col, y_col, color_col] if col]
                missing_cols = [col for col in required_cols if col and col not in df.columns]
                
                if missing_cols:
                    st.warning(f"⚠️ Chart needs columns: {', '.join(missing_cols)} from {item.get('dataset_source')}")
                else:
                    create_chart(chart_data, df, f"canvas_{index}", allow_chart_selection=False)
                    
            except Exception as e:
                st.warning(f"⚠️ Chart from: {item.get('dataset_source', 'Unknown')}")
        
        st.divider()

def suggest_alternatives(missing_cols, available_cols):
    """Suggest similar column names"""
    suggestions = {}
    for missing in missing_cols:
        if missing:
            # Simple similarity matching
            similar = [col for col in available_cols if missing.lower() in col.lower() or col.lower() in missing.lower()]
            if similar:
                suggestions[missing] = similar
    
    if suggestions:
        st.markdown("**Suggested alternatives:**")
        for missing, alternatives in suggestions.items():
            st.markdown(f"- Instead of `{missing}`, try: {', '.join(alternatives)}")

def create_chart(chart_data, df, msg_key, allow_chart_selection=False):
    """Enhanced chart creation with more chart types and color options"""
    try:
        x_col = chart_data.get("x_column")
        y_col = chart_data.get("y_column")
        color_col = chart_data.get("color_column")
        title = chart_data.get("title", "Chart")
        default_chart_type = chart_data.get("chart_type", "bar")
        
        # Validate columns exist
        required_cols = [col for col in [x_col, y_col, color_col] if col]
        missing_cols = [col for col in required_cols if col and col not in df.columns]
        
        if missing_cols:
            # Silent fail - just return False, caller handles the messaging
            return False
        
        # EXPANDED Chart types with categories
        chart_categories = {
            "📊 Basic": ["bar", "line", "scatter", "area"],
            "🥧 Parts of Whole": ["pie", "donut", "treemap", "sunburst"],
            "📈 Distribution": ["histogram", "box", "violin"],
            "🔥 Advanced": ["heatmap", "funnel", "waterfall"],
        }
        all_chart_types = [ct for cats in chart_categories.values() for ct in cats]
        
        # Color palette presets
        color_palettes = {
            "🔴 Netflix": ["#E50914", "#B20710", "#F40612", "#831010", "#DB0000"],
            "🔵 Ocean": ["#0077B6", "#00B4D8", "#90E0EF", "#CAF0F8", "#023E8A"],
            "🟢 Forest": ["#2D6A4F", "#40916C", "#52B788", "#74C69D", "#95D5B2"],
            "🟣 Royal": ["#7209B7", "#560BAD", "#480CA8", "#3A0CA3", "#3F37C9"],
            "🌈 Rainbow": ["#E63946", "#F4A261", "#2A9D8F", "#264653", "#E9C46A"],
            "⬛ Monochrome": ["#212529", "#495057", "#6C757D", "#ADB5BD", "#DEE2E6"],
        }
        
        # Chart type and color selector (only for AI-generated charts)
        if allow_chart_selection:
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col2:
                selectbox_key = f"chart_type_{msg_key}_{hash(title)}"
                selected_chart_type = st.selectbox(
                    "Chart:",
                    options=all_chart_types,
                    index=all_chart_types.index(default_chart_type) if default_chart_type in all_chart_types else 0,
                    key=selectbox_key,
                    format_func=lambda x: x.replace("_", " ").title()
                )
            
            with col3:
                color_key = f"color_palette_{msg_key}_{hash(title)}"
                selected_palette = st.selectbox(
                    "Colors:",
                    options=list(color_palettes.keys()),
                    index=0,
                    key=color_key
                )
                color_sequence = color_palettes[selected_palette]
            
            with col1:
                pass  # Chart title space
        else:
            selected_chart_type = default_chart_type
            color_sequence = color_palettes["🔴 Netflix"]
        
        # Create and display the chart with selected colors
        fig = create_plotly_chart(df, selected_chart_type, x_col, y_col, color_col, title, color_sequence)
        
        if fig:
            st.plotly_chart(fig, use_container_width=True, key=f"chart_{msg_key}")
            return True
        return False
        
    except Exception as e:
        st.error(f"Chart creation failed: {str(e)}")
        return False

def create_plotly_chart(df, chart_type, x_col, y_col, color_col, title, color_sequence=None):
    """Create different types of charts using Plotly with custom colors"""
    import plotly.express as px
    import plotly.graph_objects as go
    
    # Default Netflix colors
    if color_sequence is None:
        color_sequence = ["#E50914", "#B20710", "#F40612", "#831010", "#DB0000"]
    
    try:
        # Validate columns exist in dataframe
        df_columns = df.columns.tolist()
        
        if x_col and x_col not in df_columns:
            st.warning(f"⚠️ Column '{x_col}' not found. Available columns: {', '.join(df_columns[:10])}")
            return None
        
        if y_col and y_col not in df_columns:
            st.warning(f"⚠️ Column '{y_col}' not found. Available columns: {', '.join(df_columns[:10])}")
            return None
        
        if color_col and color_col not in df_columns:
            # Color column is optional, just skip it
            color_col = None
        
        # Prepare data
        plot_df = df.dropna(subset=[col for col in [x_col, y_col] if col])
        
        # ==================== BASIC CHARTS ====================
        if chart_type == "bar":
            if y_col:
                if color_col:
                    fig = px.bar(plot_df, x=x_col, y=y_col, color=color_col, title=title, color_discrete_sequence=color_sequence)
                else:
                    agg_df = plot_df.groupby(x_col)[y_col].sum().reset_index()
                    fig = px.bar(agg_df, x=x_col, y=y_col, title=title, color_discrete_sequence=color_sequence)
            else:
                fig = px.bar(plot_df[x_col].value_counts().reset_index(), 
                           x='index', y=x_col, title=title, color_discrete_sequence=color_sequence)
        
        elif chart_type == "line":
            if color_col:
                fig = px.line(plot_df, x=x_col, y=y_col, color=color_col, title=title, color_discrete_sequence=color_sequence)
            else:
                agg_df = plot_df.groupby(x_col)[y_col].sum().reset_index()
                fig = px.line(agg_df, x=x_col, y=y_col, title=title, color_discrete_sequence=color_sequence)
        
        elif chart_type == "scatter":
            fig = px.scatter(plot_df, x=x_col, y=y_col, color=color_col, title=title, color_discrete_sequence=color_sequence)
        
        elif chart_type == "area":
            if color_col:
                fig = px.area(plot_df, x=x_col, y=y_col, color=color_col, title=title, color_discrete_sequence=color_sequence)
            else:
                agg_df = plot_df.groupby(x_col)[y_col].sum().reset_index()
                fig = px.area(agg_df, x=x_col, y=y_col, title=title, color_discrete_sequence=color_sequence)
        
        # ==================== PARTS OF WHOLE ====================
        elif chart_type == "pie":
            if y_col:
                pie_data = plot_df.groupby(x_col)[y_col].sum().reset_index()
                fig = px.pie(pie_data, values=y_col, names=x_col, title=title, color_discrete_sequence=color_sequence)
            else:
                pie_data = plot_df[x_col].value_counts()
                fig = px.pie(values=pie_data.values, names=pie_data.index, title=title, color_discrete_sequence=color_sequence)
        
        elif chart_type == "donut":
            if y_col:
                pie_data = plot_df.groupby(x_col)[y_col].sum().reset_index()
                fig = px.pie(pie_data, values=y_col, names=x_col, title=title, hole=0.4, color_discrete_sequence=color_sequence)
            else:
                pie_data = plot_df[x_col].value_counts()
                fig = px.pie(values=pie_data.values, names=pie_data.index, title=title, hole=0.4, color_discrete_sequence=color_sequence)
        
        elif chart_type == "treemap":
            if y_col:
                fig = px.treemap(plot_df, path=[x_col], values=y_col, title=title, color_discrete_sequence=color_sequence)
            else:
                counts = plot_df[x_col].value_counts().reset_index()
                counts.columns = [x_col, 'count']
                fig = px.treemap(counts, path=[x_col], values='count', title=title, color_discrete_sequence=color_sequence)
        
        elif chart_type == "sunburst":
            if color_col and y_col:
                fig = px.sunburst(plot_df, path=[x_col, color_col], values=y_col, title=title, color_discrete_sequence=color_sequence)
            elif y_col:
                fig = px.sunburst(plot_df, path=[x_col], values=y_col, title=title, color_discrete_sequence=color_sequence)
            else:
                fig = px.sunburst(plot_df, path=[x_col], title=title, color_discrete_sequence=color_sequence)
        
        # ==================== DISTRIBUTION ====================
        elif chart_type == "histogram":
            fig = px.histogram(plot_df, x=x_col if not y_col else y_col, color=color_col, title=title, color_discrete_sequence=color_sequence)
        
        elif chart_type == "box":
            if color_col:
                fig = px.box(plot_df, x=color_col, y=y_col or x_col, title=title, color_discrete_sequence=color_sequence)
            else:
                fig = px.box(plot_df, y=y_col or x_col, title=title, color_discrete_sequence=color_sequence)
        
        elif chart_type == "violin":
            if color_col:
                fig = px.violin(plot_df, x=color_col, y=y_col or x_col, title=title, color_discrete_sequence=color_sequence, box=True)
            else:
                fig = px.violin(plot_df, y=y_col or x_col, title=title, color_discrete_sequence=color_sequence, box=True)
        
        # ==================== ADVANCED ====================
        elif chart_type == "heatmap":
            if color_col and y_col:
                pivot = plot_df.pivot_table(values=y_col, index=x_col, columns=color_col, aggfunc='sum', fill_value=0)
                fig = px.imshow(pivot, title=title, color_continuous_scale=[[0, color_sequence[0]], [1, color_sequence[-1]]])
            else:
                # Fallback to bar
                agg_df = plot_df.groupby(x_col)[y_col].sum().reset_index() if y_col else plot_df[x_col].value_counts().reset_index()
                fig = px.bar(agg_df, x=agg_df.columns[0], y=agg_df.columns[1], title=title, color_discrete_sequence=color_sequence)
        
        elif chart_type == "funnel":
            if y_col:
                agg_df = plot_df.groupby(x_col)[y_col].sum().reset_index().sort_values(y_col, ascending=False)
                fig = px.funnel(agg_df, x=y_col, y=x_col, title=title, color_discrete_sequence=color_sequence)
            else:
                counts = plot_df[x_col].value_counts().reset_index()
                counts.columns = [x_col, 'count']
                fig = px.funnel(counts, x='count', y=x_col, title=title, color_discrete_sequence=color_sequence)
        
        elif chart_type == "waterfall":
            if y_col:
                agg_df = plot_df.groupby(x_col)[y_col].sum().reset_index()
                fig = go.Figure(go.Waterfall(
                    name="", orientation="v",
                    x=agg_df[x_col].tolist(),
                    y=agg_df[y_col].tolist(),
                    connector={"line": {"color": color_sequence[0]}},
                    increasing={"marker": {"color": color_sequence[0]}},
                    decreasing={"marker": {"color": color_sequence[1] if len(color_sequence) > 1 else "#FF6B6B"}},
                ))
                fig.update_layout(title=title)
            else:
                counts = plot_df[x_col].value_counts()
                fig = go.Figure(go.Waterfall(
                    name="", orientation="v",
                    x=counts.index.tolist(),
                    y=counts.values.tolist(),
                    connector={"line": {"color": color_sequence[0]}},
                ))
                fig.update_layout(title=title)
        
        else:
            # Default to bar chart
            fig = px.bar(plot_df, x=x_col, y=y_col, color=color_col, title=title, color_discrete_sequence=color_sequence)
        
        # Update layout for better appearance
        fig.update_layout(
            showlegend=True,
            height=400,
            margin=dict(t=50, b=50, l=50, r=50),
            font=dict(family="Arial, sans-serif"),
            title_font_size=16,
            title_x=0.5  # Center title
        )
        
        return fig
        
    except Exception as e:
        st.error(f"Error creating {chart_type} chart: {str(e)}")
        return None

def render_report_item(item, df, index):
    """Render canvas item in report format"""
    st.markdown(f"## 📊 {item.get('title', f'Analysis {index + 1}')}")
    
    # Show metadata
    col1, col2 = st.columns(2)
    with col1:
        st.caption(f"**Source Dataset:** {item.get('dataset_source', 'Unknown')}")
    with col2:
        st.caption(f"**Added:** {item.get('timestamp', 'Unknown')}")
    
    # Render content
    item_type = item.get("type", "unknown")
    content = item.get("content", {})
    
    if item_type == "text":
        st.markdown(content.get("text", "No content"))
        
    elif item_type == "chart":
        if "ai_context" in content:
            st.markdown("**Analysis:**")
            st.markdown(content["ai_context"])
        
        chart_data = content.get("chart_data")
        if chart_data and df is not None:
            try:
                create_chart(chart_data, df, f"report_chart_{item.get('id', index)}", allow_chart_selection=False)
            except:
                st.warning(f"⚠️ Chart requires dataset: {item.get('dataset_source')}")
                
    elif item_type == "complete":
        st.markdown("**Analysis:**")
        st.markdown(content.get("text", "No analysis"))
        
        chart_data = content.get("chart_data")
        if chart_data and df is not None:
            try:
                create_chart(chart_data, df, f"report_complete_{item.get('id', index)}", allow_chart_selection=False)
            except:
                st.warning(f"⚠️ Chart requires dataset: {item.get('dataset_source')}")
    
    st.markdown("---")

def generate_pdf_report(canvas_items, df, include_timestamp):
    """Generate and download PDF report with embedded charts"""
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib.enums import TA_CENTER
        import io
        import tempfile
        import os
        
        # Create PDF buffer
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, 
                               leftMargin=inch, rightMargin=inch,
                               topMargin=inch, bottomMargin=inch)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER
        )
        story.append(Paragraph("Analysis Report", title_style))
        story.append(Spacer(1, 20))
        
        # Add timestamp if requested
        if include_timestamp:
            timestamp_text = f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            story.append(Paragraph(timestamp_text, styles['Normal']))
            story.append(Spacer(1, 20))
        
        # Add each canvas item
        for i, item in enumerate(canvas_items):
            # Item title
            title = item.get('title', f'Analysis {i + 1}')
            story.append(Paragraph(f"{i + 1}. {title}", styles['Heading2']))
            
            # Source info
            source_text = f"<b>Source Dataset:</b> {item.get('dataset_source', 'Unknown')}"
            story.append(Paragraph(source_text, styles['Normal']))
            
            if include_timestamp:
                time_text = f"<b>Added:</b> {item.get('timestamp', 'Unknown')}"
                story.append(Paragraph(time_text, styles['Normal']))
            
            story.append(Spacer(1, 10))
            
            # Content
            text_content = item.get('text_content', '')
            if text_content:
                # Clean and format text for PDF
                clean_text = text_content.replace('\n', '<br/>')
                story.append(Paragraph(clean_text, styles['BodyText']))
                story.append(Spacer(1, 10))
            
            # Embed chart as image
            chart_data = item.get('chart_data')
            if chart_data and df is not None:
                try:
                    # Create the chart
                    fig = create_plotly_chart(
                        df, 
                        chart_data.get('chart_type', 'bar'),
                        chart_data.get('x_column'),
                        chart_data.get('y_column'),
                        chart_data.get('color_column'),
                        chart_data.get('title', 'Chart')
                    )
                    
                    if fig:
                        # Save chart as high-res image
                        tmp_path = tempfile.mktemp(suffix='.png')
                        
                        try:
                            # Remove engine parameter - let plotly auto-detect
                            fig.write_image(tmp_path, width=800, height=500, scale=2)
                            
                            # Verify image was created successfully
                            if os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 0:
                                # Add image to PDF
                                img = Image(tmp_path, width=5*inch, height=3*inch)
                                story.append(img)
                            else:
                                raise ValueError("Chart image file is empty or not created")
                            
                        except Exception as img_error:
                            # Fallback: Add chart description if image creation fails
                            chart_desc = f"<i>Chart: {chart_data.get('title', 'Visualization')} - {chart_data.get('chart_type', 'chart')}</i><br/>"
                            chart_desc += f"<i>X: {chart_data.get('x_column', 'N/A')}, Y: {chart_data.get('y_column', 'N/A')}</i><br/>"
                            chart_desc += f"<i>(Chart rendering unavailable: {str(img_error)[:80]})</i>"
                            story.append(Paragraph(chart_desc, styles['Italic']))
                            story.append(Spacer(1, 10))
                        finally:
                            # Clean up temp file
                            if os.path.exists(tmp_path):
                                try:
                                    os.unlink(tmp_path)
                                except:
                                    pass
                    else:
                        # Fig creation failed
                        chart_desc = f"<i>Chart: {chart_data.get('title', 'Visualization')} (rendering failed)</i>"
                        story.append(Paragraph(chart_desc, styles['Italic']))
                        
                except Exception as chart_error:
                    # If chart fails, add detailed text description
                    chart_desc = f"<i>Chart: {chart_data.get('title', 'Visualization')} ({chart_data.get('chart_type', 'chart')})</i><br/>"
                    chart_desc += f"<i>Error: {str(chart_error)[:100]}</i>"
                    story.append(Paragraph(chart_desc, styles['Italic']))
            
            story.append(Spacer(1, 20))
            
            # Add page break between items (except last one)
            if i < len(canvas_items) - 1:
                story.append(PageBreak())
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        return buffer.getvalue()
        
    except ImportError as ie:
        st.error(f"PDF generation requires additional libraries: {str(ie)}")
        st.info("Install with: pip install reportlab kaleido")
        return None
    except Exception as e:
        st.error(f"PDF generation failed: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        return None

def generate_html_report(canvas_items, df, include_timestamp):
    """Generate and download HTML report with interactive charts"""
    try:
        import plotly.io as pio
        
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Analysis Report</title>
            <meta charset="utf-8">
            <style>
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 40px;
                    background-color: #f5f5f5;
                }
                .header {
                    text-align: center;
                    margin-bottom: 40px;
                    padding: 30px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    border-radius: 10px;
                }
                .header h1 {
                    margin: 0;
                    font-size: 36px;
                }
                .timestamp {
                    color: #e0e0e0;
                    margin-top: 10px;
                }
                .item {
                    background-color: white;
                    margin-bottom: 30px;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                }
                .item-title {
                    color: #333;
                    font-size: 24px;
                    margin-bottom: 10px;
                    border-bottom: 3px solid #667eea;
                    padding-bottom: 10px;
                }
                .item-meta {
                    color: #666;
                    font-size: 14px;
                    margin-bottom: 20px;
                }
                .item-content {
                    line-height: 1.8;
                    color: #444;
                    margin-bottom: 20px;
                }
                .chart-container {
                    margin: 20px 0;
                }
            </style>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        </head>
        <body>
            <div class="header">
                <h1>📊 Analysis Report</h1>
        """
        
        if include_timestamp:
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            html_content += f'<div class="timestamp">Generated on: {timestamp}</div>'
        
        html_content += """
            </div>
        """
        
        # Add each canvas item
        for i, item in enumerate(canvas_items):
            title = item.get('title', f'Analysis {i + 1}')
            dataset = item.get('dataset_source', 'Unknown')
            timestamp = item.get('timestamp', 'Unknown')
            text_content = item.get('text_content', '')
            
            html_content += f"""
            <div class="item">
                <div class="item-title">{i + 1}. {title}</div>
                <div class="item-meta">
                    <strong>Dataset:</strong> {dataset}
            """
            
            if include_timestamp:
                html_content += f' | <strong>Added:</strong> {timestamp}'
            
            html_content += '</div>'
            
            if text_content:
                # Convert markdown-style formatting to HTML
                formatted_text = text_content.replace('\n', '<br/>')
                formatted_text = formatted_text.replace('**', '<strong>').replace('**', '</strong>')
                html_content += f'<div class="item-content">{formatted_text}</div>'
            
            # Embed interactive chart
            chart_data = item.get('chart_data')
            if chart_data and df is not None:
                try:
                    fig = create_plotly_chart(
                        df,
                        chart_data.get('chart_type', 'bar'),
                        chart_data.get('x_column'),
                        chart_data.get('y_column'),
                        chart_data.get('color_column'),
                        chart_data.get('title', 'Chart')
                    )
                    
                    if fig:
                        chart_html = pio.to_html(fig, include_plotlyjs=False, div_id=f'chart_{i}')
                        html_content += f'<div class="chart-container">{chart_html}</div>'
                        
                except Exception as chart_error:
                    html_content += f'<p><em>Chart: {chart_data.get("title", "Visualization")}</em></p>'
            
            html_content += '</div>'
        
        html_content += """
        </body>
        </html>
        """
        
        return html_content
        
    except Exception as e:
        st.error(f"HTML generation failed: {str(e)}")
        return None