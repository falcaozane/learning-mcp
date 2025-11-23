import streamlit as st
import asyncio
import nest_asyncio
import json
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import sys
import os
import google.generativeai as genai
import ast # Required for parsing list strings

# Patch Event Loop
nest_asyncio.apply()

st.set_page_config(layout="wide", page_title="Indian Stock AI Analyst")

# --- CSS Styling ---
st.markdown("""
<style>
    .stChatInput {position: fixed; bottom: 0px; z-index: 100;}
    .block-container {padding-bottom: 120px;}
</style>
""", unsafe_allow_html=True)

# =========================================================
# 1. HELPER FUNCTIONS (Moved to Top for Scope Safety)
# =========================================================
SERVER_SCRIPT = "main.py" 

async def call_mcp_tool(tool_name, args):
    """Async worker to connect to MCP and run a tool"""
    # Ensure we use the current python executable
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[SERVER_SCRIPT],
        env=os.environ.copy()
    )
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, args)
                if hasattr(result, 'content') and result.content:
                    return result.content[0].text
                return None
    except Exception as e:
        return json.dumps({"error": str(e)})

def run_sync_tool(tool_name, args):
    """Wrapper to run async MCP tools in synchronous Streamlit"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(call_mcp_tool(tool_name, args))

# =========================================================
# 2. SIDEBAR CONFIGURATION (Updated with Select All)
# =========================================================
with st.sidebar:
    st.header("⚙️ Settings")
    
    # API Key Input
    api_key = st.text_input("Gemini API Key", type="password", help="Get it from aistudio.google.com")
    if api_key:
        os.environ["GEMINI_API_KEY"] = api_key
        genai.configure(api_key=api_key)
    
    st.markdown("---")
    
    # --- Dynamic Indicator Loading ---
    st.subheader("📊 Available Indicators")
    
    # 1. Fetch Indicators (Cached)
    if "available_indicators" not in st.session_state:
        try:
            with st.spinner("Fetching tools from MCP Server..."):
                response = run_sync_tool("list_available_indicators", {})
                if response:
                    import ast
                    st.session_state.available_indicators = ast.literal_eval(response)
                else:
                    st.session_state.available_indicators = []
        except Exception as e:
            st.error(f"MCP Connection Error: {e}")
            st.session_state.available_indicators = []
    
    st.json(st.session_state.available_indicators, expanded=False)

    # 2. Select All / Clear Buttons
    if st.session_state.available_indicators:
        col1, col2 = st.columns(2)
        
        # Initialize selection state if not exists
        if "selected_indicators" not in st.session_state:
            st.session_state.selected_indicators = ["SMA", "RSI"] # Default

        if col1.button("✅ Select All"):
            st.session_state.selected_indicators = st.session_state.available_indicators
            st.rerun()
            
        if col2.button("❌ Clear"):
            st.session_state.selected_indicators = []
            st.rerun()

        # 3. The Widget (Linked to Session State)
        if hasattr(st, "pills"):
            st.pills(
                "Active Indicators", 
                st.session_state.available_indicators, 
                selection_mode="multi",
                key="selected_indicators" # This syncs with the buttons above
            )
        else:
            st.multiselect(
                "Active Indicators", 
                st.session_state.available_indicators,
                key="selected_indicators"
            )
    else:
        st.warning("No indicators found on server.")

# =========================================================
# 3. AI & VISUALIZATION LOGIC (Updated to use Selection)
# =========================================================

def parse_intent_with_ai(user_query):
    """
    Uses Gemini Flash to intelligently extract structured data.
    Uses Sidebar selections as the default if no specific indicators are mentioned.
    """
    if not os.environ.get("GEMINI_API_KEY"):
        st.warning("⚠️ Please enter your Gemini API Key in the sidebar.")
        return "RELIANCE.NS", ["SMA"]

    # Get User Preferences from Sidebar
    user_defaults = st.session_state.get("selected_indicators", ["SMA", "RSI"])
    
    try:
        model = genai.GenerativeModel('models/gemini-2.0-flash')
        
        prompt = f"""
        You are a financial intent parser for Indian Stocks.
        User Query: "{user_query}"
        
        Current User Sidebar Selection: {user_defaults}
        
        Tasks:
        1. Extract the Stock Symbol (Default to NSE suffix .NS).
        2. Identify Indicators. 
           - If the user EXPLICITLY names indicators (e.g. "Show MACD"), use only those.
           - If the user is VAGUE (e.g. "Analyze Reliance", "How is the trend?"), use the "Current User Sidebar Selection" list provided above.
           - If the sidebar selection is empty and the user is vague, default to ["SMA", "RSI"].
        
        Output strictly in this JSON format:
        {{
            "symbol": "TICKER.NS",
            "indicators": ["IND1", "IND2"],
            "period": "1y" 
        }}
        """
        
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        
        data = json.loads(response.text)
        return data["symbol"], data["indicators"]

    except Exception as e:
        st.error(f"AI Parsing Error: {e}")
        return "RELIANCE.NS", ["SMA"]
    

def render_financial_chart(data, ticker):
    """Draws a Professional Plotly Chart"""
    
    if "error" in data:
        st.error(data["error"])
        return go.Figure()

    dates = pd.to_datetime(data['dates'])
    close = data['Close']
    indicators = data['indicators']
    
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.05, row_heights=[0.6, 0.4],
                        subplot_titles=(f"{ticker} Price Action", "Technical Indicators"))

    # 1. Price Chart
    fig.add_trace(go.Scatter(x=dates, y=close, name="Close Price", line=dict(color='teal', width=1)), row=1, col=1)

    # 2. Indicators
    colors = ['#2962FF', '#FF6D00', '#00C853', "#E8F900", "#FF17F3"]
    color_idx = 0
    
    for name, values in indicators.items():
        clean_values = [v if v is not None else float('nan') for v in values]
        valid_vals = [v for v in clean_values if pd.notnull(v)]
        
        if not valid_vals: continue
        
        avg_val = sum(valid_vals) / len(valid_vals)
        current_color = colors[color_idx % len(colors)]
        
        # Heuristic: Overlay vs Oscillator
        if avg_val > (sum(close)/len(close)) * 0.2: 
            fig.add_trace(go.Scatter(x=dates, y=clean_values, name=name, line=dict(width=1.5, color=current_color)), row=1, col=1)
        else:
            fig.add_trace(go.Scatter(x=dates, y=clean_values, name=name, line=dict(width=1.5, color=current_color)), row=2, col=1)
            
            if "RSI" in name or "STOCH" in name:
                fig.add_hline(y=70, line_dash="dot", row=2, col=1, line_color="red", opacity=0.3)
                fig.add_hline(y=30, line_dash="dot", row=2, col=1, line_color="green", opacity=0.3)
                
        color_idx += 1

    fig.update_layout(height=700, template="plotly_white", hovermode="x unified")
    return fig

# =========================================================
# 4. MAIN APP INTERFACE
# =========================================================

st.title("🤖 AlgoTrader Chat (Powered by Gemini and MCP)")

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "chart_data" in message:
            fig = render_financial_chart(message["chart_data"], message["ticker"])
            st.plotly_chart(fig, use_container_width=True)

# User Input
if prompt := st.chat_input("Ask: 'How is the momentum for Tata Motors?'"):
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("🧠 AI Parsing Intent & Fetching Data..."):
            
            # 1. AI Intent Parsing
            symbol, indicators = parse_intent_with_ai(prompt)
            
            # 2. Call MCP Server
            response_json = run_sync_tool("get_historical_technicals", {
                "symbol": symbol,
                "indicators": indicators,
                "period": "1y"
            })
            
            if response_json:
                data = json.loads(response_json)
                
                if "dates" in data:
                    # Success: Construct Response
                    text_response = f"**Analysis for {symbol}**\n\nGenerated Indicators: `{', '.join(indicators)}`"
                    
                    st.markdown(text_response)
                    fig = render_financial_chart(data, symbol)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": text_response,
                        "chart_data": data,
                        "ticker": symbol
                    })
                else:
                    err = data.get("error", "Unknown error")
                    st.error(f"Server Error: {err}")
            else:
                st.error("Failed to connect to MCP Server.")