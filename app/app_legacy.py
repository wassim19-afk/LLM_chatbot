# app/app.py
# This is the Streamlit frontend for the AI-Powered BI Chatbot.
# It provides a user interface to interact with the FastAPI backend.

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
import plotly.express as px
import streamlit as st
import requests
from config.settings import settings
from utils.visualization_helper import (
    detect_chart_type, ChartType, prepare_line_chart_data, 
    prepare_bar_chart_data, get_metric_value
)
from services.response_guard import detect_intent


IDENTIFIER_KEYWORDS = ["id", "no_", "no", "entry", "document", "code", "ref", "number"]
MEASURE_KEYWORDS = ["amount", "total", "sales", "revenue", "ca", "sum", "count", "balance", "quantity", "qty", "value"]

# Configure Streamlit page
st.set_page_config(
    page_title="AI BI Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for beautiful design
st.markdown("""
<style>
    /* Main background and text colors */
    :root {
        --primary-color: #6366f1;
        --secondary-color: #8b5cf6;
        --success-color: #10b981;
        --danger-color: #ef4444;
        --warning-color: #f59e0b;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        padding: 40px 20px;
        border-radius: 15px;
        color: white;
        margin-bottom: 30px;
        box-shadow: 0 10px 30px rgba(99, 102, 241, 0.2);
    }
    
    .main-header h1 {
        margin: 0;
        font-size: 2.5em;
        font-weight: 800;
        letter-spacing: -1px;
    }
    
    .main-header p {
        margin: 10px 0 0 0;
        font-size: 1.1em;
        opacity: 0.95;
    }
    
    /* Input section styling */
    .input-section {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.05) 0%, rgba(139, 92, 246, 0.05) 100%);
        padding: 25px;
        border-radius: 12px;
        border: 2px solid rgba(99, 102, 241, 0.1);
        margin-bottom: 30px;
    }
    
    /* Subheader styling */
    .section-header {
        color: white;
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        font-size: 1.3em;
        font-weight: 700;
        margin-top: 25px;
        margin-bottom: 15px;
        padding: 12px 18px;
        border-radius: 8px;
        border: none;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        color: white;
        border: none;
        padding: 12px 40px;
        font-size: 1em;
        font-weight: 600;
        border-radius: 8px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(99, 102, 241, 0.4);
    }
    
    /* Radio button styling */
    .stRadio > label {
        font-weight: 600;
        color: #1f2937;
    }
    
    /* Success/Info/Warning boxes */
    .stSuccess, .stInfo, .stWarning, .stError {
        border-radius: 10px;
        padding: 15px 20px;
        margin: 15px 0;
    }
    
    /* Code block styling */
    .stCode {
        border-radius: 8px;
        border: 1px solid rgba(99, 102, 241, 0.2);
    }
</style>
""", unsafe_allow_html=True)

# Title section with gradient
st.markdown("""
<div class="main-header">
    <h1>🤖 AI-Powered BI Chatbot</h1>
    <p>✨ Ask questions in natural language and get SQL queries, data, and beautiful visualizations!</p>
</div>
""", unsafe_allow_html=True)

# API endpoint
API_URL = f"http://127.0.0.1:{settings.API_PORT}/api/chat"


def render_visualization(data_rows: list, columns: list = None, question: str = ""):
    """
    Render intelligent visualization based on data shape.
    Uses visualization_helper to auto-detect chart type.
    User can override the chart type with a prominent dropdown.
    """
    if not data_rows:
        st.info("No visualization available - no data returned.")
        return
    
    if not columns:
        columns = list(data_rows[0].keys()) if data_rows else []
    
    st.markdown('<div class="section-header">📈 Data Visualization</div>', unsafe_allow_html=True)
    
    # Detect chart type
    auto_chart_type = detect_chart_type(columns, data_rows)

    # For overdue customer questions, table is usually the clearest default view.
    question_lower = (question or "").lower()
    if ("client" in question_lower or "customer" in question_lower) and (
        "retard" in question_lower or "overdue" in question_lower or "late" in question_lower or "impay" in question_lower
    ):
        auto_chart_type = ChartType.TABLE

    intent = detect_intent(question)
    if intent and intent.name in {"overdue_customers", "ledger_entries"}:
        auto_chart_type = ChartType.TABLE

    def is_identifier_like(column_name: str) -> bool:
        lower_name = column_name.lower()
        return any(keyword in lower_name for keyword in IDENTIFIER_KEYWORDS)

    def is_measure_like(column_name: str) -> bool:
        lower_name = column_name.lower()
        return any(keyword in lower_name for keyword in MEASURE_KEYWORDS)

    meaningful_numeric_cols = [
        column for column in columns
        if column in columns and not is_identifier_like(column) and is_measure_like(column)
    ]
    
    # PROMINENT chart type selector using RADIO buttons
    st.write("**Select Visualization Type:**")
    chart_choices = ["Auto (Auto-Detect)", "Metric (Single Value)", "Line (Time Series)", "Bar (Categories)", "Pie (Composition)", "Table (Raw Data)"]
    chart_selected_str = st.radio(
        "💡 Choose how to display data:",
        chart_choices,
        index=0,
        horizontal=True,
    )
    
    # Parse selection
    if "Auto" in chart_selected_str:
        selected_type = auto_chart_type
        st.info(f"✨ Auto-detected chart type: **{auto_chart_type.name}**")
    elif "Metric" in chart_selected_str:
        selected_type = ChartType.METRIC
    elif "Line" in chart_selected_str:
        selected_type = ChartType.LINE
    elif "Bar" in chart_selected_str:
        selected_type = ChartType.BAR
    elif "Pie" in chart_selected_str:
        selected_type = "PIE"
    else:
        selected_type = ChartType.TABLE
    
    # Render based on selected type
    if selected_type == ChartType.METRIC:
        metric_value = get_metric_value(data_rows)
        if metric_value is not None and meaningful_numeric_cols:
            col_name = list(data_rows[0].keys())[0] if data_rows else "Value"
            st.metric(
                label=col_name, 
                value=f"{metric_value:,.2f}" if isinstance(metric_value, (int, float)) else str(metric_value)
            )
        else:
            st.warning("Could not extract metric value. Showing table.")
            st.dataframe(data_rows, use_container_width=True)
    
    elif selected_type == ChartType.LINE:
        df = prepare_line_chart_data(columns, data_rows)
        
        if df is not None and not df.empty and len(df) > 0:
            # Use first date column and first numeric column
            date_cols = [c for c in columns if any(k in c.lower() for k in ['date', 'month', 'posting', 'time', 'year'])]
            numeric_cols = [c for c in columns if c in df.columns and df[c].dtype in ['int64', 'float64'] and not is_identifier_like(c) and is_measure_like(c)]
            
            if date_cols and numeric_cols:
                try:
                    fig = px.line(
                        df,
                        x=date_cols[0],
                        y=numeric_cols[0],
                        markers=True,
                        title=f"<b>{numeric_cols[0]} over {date_cols[0]}</b>",
                        template="plotly_white",
                    )
                    # Beautiful styling
                    fig.update_traces(
                        line=dict(color='#6366f1', width=3),
                        marker=dict(size=8, color='#8b5cf6', line=dict(color='white', width=2))
                    )
                    fig.update_layout(
                        height=480,
                        hovermode='x unified',
                        font=dict(family="Arial, sans-serif", size=12, color='#1f2937'),
                        title_font_size=16,
                        xaxis_title_font=dict(size=13, color='#1f2937'),
                        yaxis_title_font=dict(size=13, color='#1f2937'),
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        margin=dict(l=60, r=40, t=60, b=60),
                    )
                    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(99, 102, 241, 0.1)')
                    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(99, 102, 241, 0.1)')
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as chart_error:
                    st.warning(f"Could not render line chart: {str(chart_error)}. Showing table instead.")
                    st.dataframe(data_rows, use_container_width=True)
            else:
                st.warning("Not enough columns for line chart. Showing table instead.")
                st.dataframe(data_rows, use_container_width=True)
        else:
            st.warning("Could not format data for line chart. Showing table instead.")
            st.dataframe(data_rows, use_container_width=True)
    
    elif selected_type == ChartType.BAR:
        df = prepare_bar_chart_data(columns, data_rows, top_n=50)  # Prepare with max 50 first
        
        if df is not None and not df.empty and len(df) > 0:
            # Try to find numeric and label columns
            numeric_cols = [col for col in df.columns if df[col].dtype in ['int64', 'float64'] and not is_identifier_like(col) and is_measure_like(col)]
            label_cols = [col for col in df.columns if col not in numeric_cols]
            
            # If we have both, create the bar chart
            if len(numeric_cols) > 0 and len(label_cols) > 0:
                # Only show slider if we have more than 5 rows to work with
                if len(df) > 5:
                    st.write("**Adjust number of rows displayed:**")
                    top_n = st.slider("📊 Show top N rows:", 5, min(50, len(df)), min(10, len(df)), key="bar_top_n")
                    df = prepare_bar_chart_data(columns, data_rows, top_n=top_n)
                else:
                    top_n = len(df)
                
                try:
                    fig = px.bar(
                        df,
                        x=label_cols[0],
                        y=numeric_cols[0],
                        title=f"<b>Top {len(df)} by {numeric_cols[0]}</b>",
                        template="plotly_white",
                        color=numeric_cols[0],
                        color_continuous_scale=['#6366f1', '#8b5cf6', '#a78bfa'],
                    )
                    # Beautiful styling
                    fig.update_traces(
                        marker_line_color='rgba(255,255,255,0.3)',
                        marker_line_width=1.5,
                        hovertemplate='<b>%{x}</b><br>%{y:,.0f}<extra></extra>',
                    )
                    fig.update_layout(
                        height=480,
                        font=dict(family="Arial, sans-serif", size=12, color='#1f2937'),
                        title_font_size=16,
                        xaxis_title_font=dict(size=13, color='#1f2937'),
                        yaxis_title_font=dict(size=13, color='#1f2937'),
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        margin=dict(l=60, r=40, t=60, b=80),
                        showlegend=False,
                    )
                    fig.update_xaxes(showgrid=False)
                    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(99, 102, 241, 0.1)')
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as chart_error:
                    st.warning(f"Could not render bar chart: {str(chart_error)}. Showing table instead.")
                    st.dataframe(data_rows, use_container_width=True)
            else:
                st.warning("Data doesn't have clear business measure columns for bar chart. Showing table instead.")
                st.dataframe(data_rows, use_container_width=True)
        else:
            st.warning("Could not format data for bar chart. Showing table instead.")
            st.dataframe(data_rows, use_container_width=True)
    
    elif selected_type == "PIE":
        df = pd.DataFrame(data_rows)
        numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        label_cols = [c for c in df.columns if c not in numeric_cols]
        if numeric_cols and label_cols:
            try:
                fig = px.pie(
                    df.head(20),
                    names=label_cols[0],
                    values=numeric_cols[0],
                    title=f"<b>{numeric_cols[0]} share by {label_cols[0]}</b>",
                    template="plotly_white",
                )
                fig.update_layout(height=480)
                st.plotly_chart(fig, use_container_width=True)
            except Exception:
                st.dataframe(data_rows, use_container_width=True)
        else:
            st.warning("Not enough columns for pie chart. Showing table instead.")
            st.dataframe(data_rows, use_container_width=True)

    else:  # TABLE or unknown
        st.dataframe(data_rows, use_container_width=True)

# User input section
st.markdown('<div class="input-section">', unsafe_allow_html=True)
st.markdown("### 💬 Ask Your Question")
col_model, col1, col2 = st.columns([1.2, 3.3, 1])

with col_model:
    st.write("**Model**")
    st.info("mistral")
    selected_model = "mistral"

# Keep a stable session state key for the main input widget.
if "question_input" not in st.session_state:
    st.session_state["question_input"] = ""

if "session_id" not in st.session_state:
    st.session_state["session_id"] = None

# Sidebar session management
st.sidebar.header("🔐 Session Management")
if st.session_state["session_id"]:
    st.sidebar.success(f"Session: {st.session_state['session_id'][:8]}...")
    if st.sidebar.button("🔄 Start New Session"):
        st.session_state["session_id"] = None
        st.rerun()
else:
    if st.sidebar.button("📝 Create Session"):
        try:
            resp = requests.post(
                f"http://127.0.0.1:{settings.API_PORT}/api/session",
                timeout=5
            )
            if resp.ok:
                st.session_state["session_id"] = resp.json()["session_id"]
                st.sidebar.success(f"Created: {st.session_state['session_id'][:8]}...")
                st.rerun()
        except Exception as e:
            st.sidebar.warning(f"Session creation failed: {e}")

# Sidebar analytics
st.sidebar.header("📊 System Analytics")
try:
    analytics_resp = requests.get(
        f"http://127.0.0.1:{settings.API_PORT}/api/analytics",
        timeout=5
    )
    if analytics_resp.ok:
        analytics = analytics_resp.json()
        st.sidebar.metric("Total Queries", analytics["total_queries"])
        st.sidebar.metric("Avg Response", f"{analytics['average_response_time_seconds']:.3f}s")
        st.sidebar.metric("Cache Hit Rate", f"{analytics['cache_hit_rate_percent']:.1f}%")
        st.sidebar.metric("Error Rate", f"{analytics['error_rate_percent']:.1f}%")
except Exception:
    pass

with col1:
    question = st.text_input(
        "Enter your question:", 
        placeholder="e.g., What are the top 10 customers by sales? or CA 2023 VS 2024",
        label_visibility="collapsed",
        key="question_input",
    )

with col2:
    ask_button = st.button("🔍 Ask", type="primary", use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)

if ask_button or question:
    if question.strip():
        with st.spinner("⏳ Processing your question... This may take a few seconds."):
            try:
                # Send request to FastAPI backend
                payload = {"question": question, "model": selected_model}
                if st.session_state.get("session_id"):
                    payload["session_id"] = st.session_state["session_id"]

                response = requests.post(
                    API_URL,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()

                # Update session if returned
                if data.get("session_id"):
                    st.session_state["session_id"] = data["session_id"]

                # Display results with beautiful layout
                st.markdown('<div style="margin-top: 30px;"></div>', unsafe_allow_html=True)
                st.success("✅ Query processed successfully!")
                st.caption(f"Model used: {selected_model}")
                # Simple concise answer only
                simple_answer = (data.get("insight") or "").strip()
                if simple_answer:
                    st.markdown(
                        f"""
                        <div style="background:#f8fafc;border:1px solid #cbd5e1;padding:16px 18px;border-radius:10px;margin:16px 0;">
                            <p style="margin:0;color:#0f172a;font-size:1.05em;font-weight:600;">{simple_answer}</p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                else:
                    st.warning("Aucune reponse n'a ete retournee.")

            except requests.exceptions.RequestException as e:
                error_text = ""
                if hasattr(e, 'response') and e.response is not None:
                    error_text = f"\nBackend response: {e.response.text}"
                st.error(f"❌ Error connecting to the backend: {str(e)}{error_text}")
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
    else:
        st.warning("Please enter a question.")

# Sidebar with information
st.sidebar.header("About")
st.sidebar.markdown("""
This chatbot converts natural language questions into SQL queries,
executes them against your database, and provides insights.

**Backend**: FastAPI + LLM (Ollama Mistral)
**Frontend**: Streamlit with Plotly
**Database**: SQL Server
**Cache**: In-memory LRU (7 min TTL)
""")

st.sidebar.header("Available Schema")
try:
    schema_response = requests.get(f"http://127.0.0.1:{settings.API_PORT}/api/schema", timeout=5)
    if schema_response.ok:
        schema_list = schema_response.json()
        if schema_list:
            for schema_line in schema_list[:20]:
                st.sidebar.markdown(f"- `{schema_line}`")
            if len(schema_list) > 20:
                st.sidebar.markdown(f"...and {len(schema_list) - 20} more lines")
        else:
            st.sidebar.markdown("No schema metadata available.")
    else:
        st.sidebar.markdown("Unable to load schema metadata from backend.")
except requests.exceptions.RequestException:
    st.sidebar.markdown("Schema metadata unavailable. Ensure backend is running.")

st.sidebar.header("Setup")
st.sidebar.markdown("""
1. Ensure the FastAPI backend is running.
2. Configure your database in `.env`.
3. Make sure Ollama is running with `mistral`.
""")