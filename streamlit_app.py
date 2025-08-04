"""
Streamlit UI for the Equal-Weighted Stock Index Service

A modern, materialistic interface for building and analyzing stock indices.
"""

import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
import io
import base64

# Page configuration
st.set_page_config(
    page_title="Stock Index Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for materialistic design
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        border-left: 4px solid #667eea;
        margin-bottom: 1rem;
    }
    
    .success-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    .error-card {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    .stButton > button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.5rem 2rem;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
    
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
    }
</style>
""", unsafe_allow_html=True)

# API Configuration
API_BASE_URL = "http://localhost:8001/api/v1"

def check_api_health():
    """Check if the API is running."""
    try:
        response = requests.get(f"{API_BASE_URL.replace('/api/v1', '')}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def build_index(start_date, end_date, top_n):
    """Build the stock index."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/build-index",
            json={
                "start_date": start_date,
                "end_date": end_date,
                "top_n": top_n
            },
            timeout=30
        )
        return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_index_composition(date):
    """Get index composition for a specific date."""
    try:
        response = requests.get(f"{API_BASE_URL}/index-composition?date={date}")
        return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_index_performance(start_date, end_date):
    """Get index performance for a date range."""
    try:
        response = requests.get(f"{API_BASE_URL}/index-performance?start_date={start_date}&end_date={end_date}")
        return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_composition_changes(start_date, end_date):
    """Get composition changes for a date range."""
    try:
        response = requests.get(f"{API_BASE_URL}/composition-changes?start_date={start_date}&end_date={end_date}")
        return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}

def export_data(start_date, end_date):
    """Export data to Excel."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/export-data",
            json={
                "start_date": start_date,
                "end_date": end_date
            },
            timeout=60
        )
        return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}

def create_performance_chart(performance_data):
    """Create a performance chart using Plotly."""
    try:
        if not performance_data.get("success") or not performance_data.get("daily_returns"):
            return None
        
        df = pd.DataFrame(performance_data["daily_returns"])
        
        # Check if required columns exist
        required_columns = ['date', 'daily_return', 'cumulative_return']
        if not all(col in df.columns for col in required_columns):
            print(f"Missing columns. Available: {list(df.columns)}")
            return None
        
        df['date'] = pd.to_datetime(df['date'])
        
        fig = go.Figure()
        
        # Cumulative return line
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['cumulative_return'],
            mode='lines+markers',
            name='Cumulative Return (%)',
            line=dict(color='#667eea', width=3),
            marker=dict(size=8)
        ))
        
        # Daily return bars
        fig.add_trace(go.Bar(
            x=df['date'],
            y=df['daily_return'],
            name='Daily Return (%)',
            marker_color='#764ba2',
            opacity=0.7
        ))
        
        fig.update_layout(
            title="Index Performance Over Time",
            xaxis_title="Date",
            yaxis_title="Return (%)",
            template="plotly_white",
            height=500,
            showlegend=True
        )
        
        return fig
    except Exception as e:
        print(f"Error creating performance chart: {e}")
        return None

def create_composition_chart(composition_data):
    """Create a composition chart using Plotly."""
    try:
        if not composition_data.get("success") or not composition_data.get("stocks"):
            return None
        
        stocks = composition_data["stocks"]
        symbols = [stock["symbol"] for stock in stocks]
        weights = [stock["weight"] * 100 for stock in stocks]
        market_caps = [stock["market_cap"] / 1e12 for stock in stocks]  # Convert to trillions
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=symbols,
            y=weights,
            name='Weight (%)',
            marker_color='#667eea',
            text=[f'{w:.1f}%' for w in weights],
            textposition='auto'
        ))
        
        fig.update_layout(
            title="Index Composition by Weight",
            xaxis_title="Stock Symbol",
            yaxis_title="Weight (%)",
            template="plotly_white",
            height=400,
            showlegend=False
        )
        
        return fig
    except Exception as e:
        print(f"Error creating composition chart: {e}")
        return None

# Main application
def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>📈 Equal-Weighted Stock Index Dashboard</h1>
        <p>Build, analyze, and track custom stock indices with real-time data</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.markdown("## 🎛️ Configuration")
    
    # API Health Check
    api_healthy = check_api_health()
    if api_healthy:
        st.sidebar.success("✅ API Connected")
    else:
        st.sidebar.error("❌ API Not Available")
        st.sidebar.info("Please ensure the FastAPI service is running on localhost:8001")
        return
    
    # Data availability info
    st.sidebar.info("📊 **Available Data**: 2024-12-16")
    st.sidebar.info("💡 **Tip**: Use 2024-12-16 for testing")
    
    # Date inputs
    st.sidebar.markdown("### 📅 Date Range")
    start_date = st.sidebar.date_input(
        "Start Date",
        value=datetime(2024, 12, 16),  # Use date with available data
        max_value=datetime.now()
    )
    
    end_date = st.sidebar.date_input(
        "End Date",
        value=datetime(2024, 12, 16),  # Use date with available data
        max_value=datetime.now()
    )
    
    # Top N selection
    top_n = st.sidebar.slider("Top N Stocks", min_value=10, max_value=500, value=100, step=10)
    
    # Convert dates to string format
    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")
    
    # Main content
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏗️ Build Index", "📊 Performance", "📋 Composition", "🔄 Changes", "📤 Export"])
    
    # Tab 1: Build Index
    with tab1:
        st.markdown("## 🏗️ Build Stock Index")
        st.markdown("Build an equal-weighted index from the top stocks by market capitalization.")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if st.button("🚀 Build Index", key="build_index"):
                with st.spinner("Building index..."):
                    result = build_index(start_date_str, end_date_str, top_n)
                    
                    if result.get("success"):
                        st.markdown(f"""
                        <div class="success-card">
                            <h3>✅ Index Built Successfully!</h3>
                            <p><strong>Date Range:</strong> {result.get('date_range', 'N/A')}</p>
                            <p><strong>Total Dates Processed:</strong> {result.get('total_dates_processed', 0)}</p>
                            <p><strong>Compositions Built:</strong> {result.get('total_compositions_built', 0)}</p>
                            <p><strong>Performance Calculated:</strong> {result.get('total_performance_calculated', 0)}</p>
                            <p><strong>Top N:</strong> {result.get('top_n', 0)}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        error_msg = result.get('error', 'Unknown error')
                        st.markdown(f"""
                        <div class="error-card">
                            <h3>❌ Error Building Index</h3>
                            <p><strong>Error:</strong> {error_msg}</p>
                            <p><strong>Request Details:</strong></p>
                            <ul>
                                <li>Start Date: {start_date_str}</li>
                                <li>End Date: {end_date_str}</li>
                                <li>Top N: {top_n}</li>
                            </ul>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Show debug info
                        with st.expander("🔍 Debug Information"):
                            st.json(result)
        
        with col2:
            st.markdown("### 📈 Quick Stats")
            st.markdown(f"""
            <div class="metric-card">
                <h4>Date Range</h4>
                <p>{start_date_str} to {end_date_str}</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="metric-card">
                <h4>Top N Stocks</h4>
                <p>{top_n}</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Tab 2: Performance
    with tab2:
        st.markdown("## 📊 Index Performance")
        st.markdown("View historical performance and returns.")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if st.button("📈 Load Performance", key="load_performance"):
                with st.spinner("Loading performance data..."):
                    performance_data = get_index_performance(start_date_str, end_date_str)
                    
                    if performance_data.get("success"):
                        # Display performance metrics
                        col_a, col_b, col_c, col_d = st.columns(4)
                        
                        with col_a:
                            st.metric(
                                "Total Return (%)",
                                f"{performance_data.get('total_return', 0):.2f}%"
                            )
                        
                        with col_b:
                            st.metric(
                                "Start Date",
                                start_date_str
                            )
                        
                        with col_c:
                            st.metric(
                                "End Date",
                                end_date_str
                            )
                        
                        with col_d:
                            st.metric(
                                "Trading Days",
                                len(performance_data.get("daily_returns", []))
                            )
                        
                        # Performance chart
                        fig = create_performance_chart(performance_data)
                        if fig:
                            st.plotly_chart(fig, use_container_width=True)
                        
                        # Performance table
                        if performance_data.get("daily_returns"):
                            df = pd.DataFrame(performance_data["daily_returns"])
                            st.markdown("### 📋 Daily Performance Data")
                            st.dataframe(df, use_container_width=True)
                    else:
                        st.error(f"Error loading performance: {performance_data.get('error', 'Unknown error')}")
        
        with col2:
            st.markdown("### 📊 Performance Metrics")
            st.markdown("""
            <div class="metric-card">
                <h4>Total Return</h4>
                <p>Overall return over the period</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="metric-card">
                <h4>Daily Returns</h4>
                <p>Day-by-day performance</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="metric-card">
                <h4>Cumulative Returns</h4>
                <p>Running total performance</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Tab 3: Composition
    with tab3:
        st.markdown("## 📋 Index Composition")
        st.markdown("View the current composition of the index.")
        
        # Date selector for composition
        composition_date = st.date_input(
            "Select Date for Composition",
            value=datetime(2024, 12, 16),  # Use date with available data
            max_value=datetime.now()
        )
        composition_date_str = composition_date.strftime("%Y-%m-%d")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if st.button("📋 Load Composition", key="load_composition"):
                with st.spinner("Loading composition data..."):
                    composition_data = get_index_composition(composition_date_str)
                    
                    if composition_data.get("success"):
                        # Display composition metrics
                        col_a, col_b, col_c = st.columns(3)
                        
                        with col_a:
                            st.metric(
                                "Total Stocks",
                                composition_data.get("total_stocks", 0)
                            )
                        
                        with col_b:
                            st.metric(
                                "Equal Weight (%)",
                                f"{composition_data.get('equal_weight', 0) * 100:.2f}%"
                            )
                        
                        with col_c:
                            st.metric(
                                "Date",
                                composition_date_str
                            )
                        
                        # Composition chart
                        fig = create_composition_chart(composition_data)
                        if fig:
                            st.plotly_chart(fig, use_container_width=True)
                        
                        # Composition table
                        if composition_data.get("stocks"):
                            df = pd.DataFrame(composition_data["stocks"])
                            st.markdown("### 📊 Stock Composition Data")
                            st.dataframe(df, use_container_width=True)
                    else:
                        st.error(f"Error loading composition: {composition_data.get('error', 'Unknown error')}")
        
        with col2:
            st.markdown("### 📋 Composition Info")
            st.markdown("""
            <div class="metric-card">
                <h4>Equal Weighting</h4>
                <p>Each stock has equal weight</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="metric-card">
                <h4>Market Cap Ranked</h4>
                <p>Stocks ranked by market cap</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="metric-card">
                <h4>Daily Rebalancing</h4>
                <p>Index rebalances daily</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Tab 4: Changes
    with tab4:
        st.markdown("## 🔄 Composition Changes")
        st.markdown("Track when stocks enter or exit the index.")
        
        if st.button("🔄 Load Changes", key="load_changes"):
            with st.spinner("Loading composition changes..."):
                changes_data = get_composition_changes(start_date_str, end_date_str)
                
                if changes_data.get("success"):
                    changes = changes_data.get("changes", [])
                    
                    if changes:
                        st.markdown(f"### 📊 Found {len(changes)} Composition Changes")
                        
                        for i, change in enumerate(changes):
                            with st.expander(f"Change on {change.get('date', 'N/A')}"):
                                col_a, col_b = st.columns(2)
                                
                                with col_a:
                                    st.markdown("**📈 Additions:**")
                                    additions = change.get("additions", [])
                                    if additions:
                                        for stock in additions:
                                            st.write(f"• {stock}")
                                    else:
                                        st.write("None")
                                
                                with col_b:
                                    st.markdown("**📉 Removals:**")
                                    removals = change.get("removals", [])
                                    if removals:
                                        for stock in removals:
                                            st.write(f"• {stock}")
                                    else:
                                        st.write("None")
                    else:
                        st.info("No composition changes found in the selected date range.")
                else:
                    st.error(f"Error loading changes: {changes_data.get('error', 'Unknown error')}")
    
    # Tab 5: Export
    with tab5:
        st.markdown("## 📤 Export Data")
        st.markdown("Export index data to Excel format.")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if st.button("📤 Export to Excel", key="export_data"):
                with st.spinner("Exporting data..."):
                    export_result = export_data(start_date_str, end_date_str)
                    
                    if export_result.get("success"):
                        st.markdown(f"""
                        <div class="success-card">
                            <h3>✅ Export Successful!</h3>
                            <p><strong>File URL:</strong> {export_result.get('file_url', 'N/A')}</p>
                            <p><strong>File Size:</strong> {export_result.get('file_size', 0)} bytes</p>
                            <p><strong>Export Date:</strong> {export_result.get('export_date', 'N/A')}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.info("The Excel file has been generated and is available for download via the API.")
                    else:
                        st.markdown(f"""
                        <div class="error-card">
                            <h3>❌ Export Failed</h3>
                            <p>{export_result.get('error', 'Unknown error')}</p>
                        </div>
                        """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("### 📤 Export Features")
            st.markdown("""
            <div class="metric-card">
                <h4>Multiple Sheets</h4>
                <p>Performance, Compositions, Summary</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="metric-card">
                <h4>Professional Format</h4>
                <p>Clean headers and formatting</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="metric-card">
                <h4>Complete Data</h4>
                <p>All index data included</p>
            </div>
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    main() 