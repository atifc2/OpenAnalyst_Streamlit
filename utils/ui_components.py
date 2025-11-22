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
    """Enhanced response rendering with smart chart generation"""
    
    if isinstance(ai_response, dict):
        content = ai_response.get("content", "")
        st.markdown(content)
        
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
                st.error(f"❌ Missing columns: {', '.join(missing_cols)}")
                st.info("Available columns: " + ", ".join(active_df.columns))
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
    """Add response to canvas - simple function"""
    # Determine title
    if chart_data:
        title = chart_data.get("title", "Analysis with Chart")
    else:
        # Use first 50 chars of text as title
        title = text_content[:50] + "..." if len(text_content) > 50 else text_content
    
    # Create canvas item
    canvas_item = {
        "title": title,
        "text_content": text_content,
        "chart_data": chart_data,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "pinned_at": datetime.datetime.now().strftime("%H:%M:%S"),
        "dataset_source": st.session_state.get("active_dataset_key", "Unknown")
    }
    
    # Add to session state
    if "canvas_items" not in st.session_state:
        st.session_state.canvas_items = []
    
    st.session_state.canvas_items.append(canvas_item)

def render_canvas_item(item, df, index):
    """Render canvas item"""
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
        
        # Show text content
        text_content = item.get("text_content", "")
        if text_content:
            st.markdown(text_content)
        
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
                    create_chart(chart_data, df, f"canvas_{index}", allow_chart_selection=True)
                    
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
    """Enhanced chart creation with conditional chart type selection"""
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
            st.error(f"❌ Missing columns: {', '.join(missing_cols)}")
            return
        
        # Chart type selector (only for AI-generated charts)
        if allow_chart_selection:
            chart_types = ["bar", "line", "scatter", "pie", "histogram", "box", "area"]
            
            selectbox_key = f"chart_type_{msg_key}_{hash(title)}"
            
            col1, col2 = st.columns([3, 1])
            with col2:
                selected_chart_type = st.selectbox(
                    "Chart Type:",
                    options=chart_types,
                    index=chart_types.index(default_chart_type) if default_chart_type in chart_types else 0,
                    key=selectbox_key
                )
            with col1:
                pass  # Chart will be displayed here
        else:
            selected_chart_type = default_chart_type
        
        # Create and display the chart
        fig = create_plotly_chart(df, selected_chart_type, x_col, y_col, color_col, title)
        
        if fig:
            st.plotly_chart(fig, use_container_width=True, key=f"chart_{msg_key}")
            return True
        return False
        
    except Exception as e:
        st.error(f"Chart creation failed: {str(e)}")
        return False

def create_plotly_chart(df, chart_type, x_col, y_col, color_col, title):
    """Create different types of charts using Plotly"""
    import plotly.express as px
    import plotly.graph_objects as go
    
    try:
        # Prepare data
        plot_df = df.dropna(subset=[col for col in [x_col, y_col] if col])
        
        if chart_type == "bar":
            if y_col:
                # Grouped bar chart
                if color_col:
                    fig = px.bar(plot_df, x=x_col, y=y_col, color=color_col, title=title)
                else:
                    # Aggregate data for bar chart
                    agg_df = plot_df.groupby(x_col)[y_col].sum().reset_index()
                    fig = px.bar(agg_df, x=x_col, y=y_col, title=title)
            else:
                # Count bar chart
                fig = px.bar(plot_df[x_col].value_counts().reset_index(), 
                           x='index', y=x_col, title=title)
        
        elif chart_type == "line":
            if color_col:
                fig = px.line(plot_df, x=x_col, y=y_col, color=color_col, title=title)
            else:
                # Aggregate for line chart
                agg_df = plot_df.groupby(x_col)[y_col].sum().reset_index()
                fig = px.line(agg_df, x=x_col, y=y_col, title=title)
        
        elif chart_type == "scatter":
            fig = px.scatter(plot_df, x=x_col, y=y_col, color=color_col, title=title)
        
        elif chart_type == "pie":
            if color_col:
                # Use color column for pie segments
                pie_data = plot_df[color_col].value_counts()
            else:
                # Use x column for pie segments
                pie_data = plot_df[x_col].value_counts()
            fig = px.pie(values=pie_data.values, names=pie_data.index, title=title)
        
        elif chart_type == "histogram":
            fig = px.histogram(plot_df, x=x_col, color=color_col, title=title)
        
        elif chart_type == "box":
            if color_col:
                fig = px.box(plot_df, x=color_col, y=y_col or x_col, title=title)
            else:
                fig = px.box(plot_df, y=y_col or x_col, title=title)
        
        elif chart_type == "area":
            if color_col:
                fig = px.area(plot_df, x=x_col, y=y_col, color=color_col, title=title)
            else:
                agg_df = plot_df.groupby(x_col)[y_col].sum().reset_index()
                fig = px.area(agg_df, x=x_col, y=y_col, title=title)
        
        else:
            # Default to bar chart
            fig = px.bar(plot_df, x=x_col, y=y_col, color=color_col, title=title)
        
        # Update layout for better appearance
        fig.update_layout(
            showlegend=True,
            height=400,
            margin=dict(t=50, b=50, l=50, r=50)
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

def generate_pdf_report(canvas_items, include_timestamp):
    """Generate and download PDF report"""
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        import io
        
        # Create PDF buffer
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1  # Center
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
            source_text = f"Source Dataset: {item.get('dataset_source', 'Unknown')}"
            story.append(Paragraph(source_text, styles['Normal']))
            
            if include_timestamp:
                time_text = f"Added: {item.get('timestamp', 'Unknown')}"
                story.append(Paragraph(time_text, styles['Normal']))
            
            story.append(Spacer(1, 10))
            
            # Content
            content = item.get('content', {})
            if content.get('text'):
                story.append(Paragraph(content['text'], styles['Normal']))
            
            # Chart info (we can't embed interactive charts in PDF, so add description)
            if content.get('chart_data'):
                chart_data = content['chart_data']
                chart_desc = f"Chart: {chart_data.get('title', 'Visualization')} ({chart_data.get('chart_type', 'Unknown type')})"
                story.append(Paragraph(chart_desc, styles['Italic']))
            
            story.append(Spacer(1, 20))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        # Download button
        st.download_button(
            label="📄 Download PDF Report",
            data=buffer.getvalue(),
            file_name=f"analysis_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mime="application/pdf"
        )
        
    except ImportError:
        st.error("PDF generation requires reportlab. Install with: pip install reportlab")
    except Exception as e:
        st.error(f"PDF generation failed: {str(e)}")