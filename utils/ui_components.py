import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

def render_plotly_chart(chart_data, df):
    """
    Renders a Plotly chart based on AI-generated chart_data.
    Handles: bar, pie, line, scatter charts with defensive error handling.
    """
    try:
        title = chart_data.get("title", "AI Generated Chart")
        chart_type = chart_data.get("chart_type", "").lower()

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
            
        else:
            st.warning(f"⚠️ Unsupported chart type: '{chart_type}'")
            st.info("Supported types: bar, pie, line, scatter")
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

def render_chat_response(msg_content, df, msg_key):
    """
    Renders an AI chat response with interactive buttons.
    Handles: text responses, charts, errors, and suggested actions.
    """
    # Check if this message is already pinned
    is_pinned = any(item == msg_content for item in st.session_state.canvas_items)
    
    # Get the text content
    content_text = msg_content.get("content", "")

    # Display based on response type
    if msg_content.get("response_type") == "error":
        st.error(content_text)
    else:
        st.markdown(content_text)

    # Render chart if present
    if msg_content.get("response_type") == "chart" and msg_content.get("chart_data"):
        # Debug view in Streamlit UI
        with st.expander("🔍 Debug: Message Content"):
            st.json(msg_content)
        render_plotly_chart(msg_content["chart_data"], df)

    # Action buttons row
    col1, col2 = st.columns([0.8, 0.2])
    
    with col1:
        # Show "Generate Chart" button for visualizable text responses
        if msg_content.get("is_visualizable") and msg_content.get("response_type") == "text":
            if st.button("📊 Generate Chart", key=f"gen_chart_{msg_key}"):
                st.session_state.messages.append({
                    "role": "user", 
                    "content": "Visualize your last insight with an appropriate chart."
                })
                st.rerun()
    
    with col2:
        # Pin/Unpin button
        if is_pinned:
            st.button("✓ Pinned", key=f"pinned_{msg_key}", disabled=True)
        else:
            if st.button("➕ Pin", key=f"pin_{msg_key}"):
                st.session_state.canvas_items.append(msg_content)
                st.toast("📌 Pinned to Canvas!", icon="✅")
                st.rerun()

    # Suggested actions
    suggested_actions = msg_content.get("suggested_actions")
    if suggested_actions and isinstance(suggested_actions, list):
        st.markdown("---")
        st.markdown("**💡 Suggested next steps:**")
        cols = st.columns(min(len(suggested_actions), 3))
        for i, action in enumerate(suggested_actions):
            if isinstance(action, str):
                col_idx = i % 3
                with cols[col_idx]:
                    if st.button(action, key=f"action_{msg_key}_{i}", use_container_width=True):
                        st.session_state.messages.append({"role": "user", "content": action})
                        st.rerun()

def render_canvas_item(item_json, df, item_index):
    """
    Renders a pinned item in the Canvas or Report view.
    Includes an unpin button for removal.
    """
    with st.container(border=True):
        col1, col2 = st.columns([0.95, 0.05])
        
        with col1:
            # Display content
            content = item_json.get("content", "")
            if content:
                st.markdown(content)
            
            # Display chart if present
            if item_json.get("response_type") == "chart" and item_json.get("chart_data"):
                render_plotly_chart(item_json["chart_data"], df)
        
        with col2:
            # Unpin button
            if st.button("🗑️", key=f"unpin_{item_index}", help="Remove from Canvas"):
                st.session_state.canvas_items.pop(item_index)
                st.toast("Removed from Canvas", icon="🗑️")
                st.rerun()