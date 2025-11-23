import streamlit as st
import asyncio
import nest_asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import sys
import os

# 1. Patch the Event Loop (Crucial for Streamlit + Async)
nest_asyncio.apply()

# 2. Configuration
st.set_page_config(page_title="Indian Stock Analyst", page_icon="📈")
SERVER_SCRIPT = "main.py"  # The file we created earlier

async def run_mcp_tool(tool_name, arguments):
    """
    Connects to the local MCP server, runs a tool, and disconnects.
    We use a fresh connection per request to keep Streamlit's state simple.
    """
    # Define how to launch the server
    server_params = StdioServerParameters(
        command=sys.executable, # Uses the same Python running Streamlit
        args=[SERVER_SCRIPT],   # Arguments for the command
        env=os.environ.copy()   # Pass current env vars (API keys, etc)
    )

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the connection
                await session.initialize()
                
                # Execute the tool
                result = await session.call_tool(tool_name, arguments)
                return result
    except Exception as e:
        return f"Error: {str(e)}"

def get_available_tools():
    """Fetches the list of tools from the server."""
    # We run the async function synchronously here
    loop = asyncio.get_event_loop()
    
    # Simple query to list tools (we manually inspect for now or hardcode)
    # Ideally, you'd call session.list_tools(), but for this UI we'll just
    # use the known tools we built.
    return ["calculate_technicals", "list_available_indicators"]

# --- Streamlit UI ---

st.title("🇮🇳 Indian Stock MCP Client")
st.markdown("Connects to your local **FastMCP** server via stdio.")

# Sidebar Controls
with st.sidebar:
    st.header("Configuration")
    ticker = st.text_input("Stock Symbol", value="RELIANCE", help="Enter just the name (e.g. TCS, INFY)")
    period = st.selectbox("Period", ["1mo", "3mo", "6mo", "1y", "2y", "5y", "max"], index=3)
    
    # Fetch available indicators dynamically
    if st.button("🔄 Refresh Indicators"):
        with st.spinner("Fetching indicators from server..."):
            loop = asyncio.get_event_loop()
            # We use the tool 'list_available_indicators' we created in server.py
            result = loop.run_until_complete(run_mcp_tool("list_available_indicators", {}))
            
            # MCP returns a list of Content objects, we need to parse the text
            if hasattr(result, 'content') and result.content:
                import ast
                # Parse the string representation of the list back to a list
                st.session_state['indicators_list'] = ast.literal_eval(result.content[0].text)
            else:
                st.error("Could not fetch indicators.")

    # Default indicators if none fetched
    if 'indicators_list' not in st.session_state:
        st.session_state['indicators_list'] = ["SMA", "RSI", "MACD", "BOLLINGER", "ADX"]

    selected_indicators = st.multiselect(
        "Select Indicators", 
        st.session_state['indicators_list'],
        default=["SMA", "RSI"]
    )

# Main Action Button
if st.button("🚀 Analyze Stock", type="primary"):
    if not ticker:
        st.warning("Please enter a ticker symbol.")
    else:
        with st.spinner(f"Asking MCP Server to analyze {ticker}..."):
            # Prepare arguments for the tool
            args = {
                "symbol": ticker,
                "indicators": selected_indicators,
                "period": period
            }
            
            # Run the async tool synchronously
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(run_mcp_tool("calculate_technicals", args))
            
            # Display Results
            st.subheader("Analysis Results")
            
            if hasattr(result, 'content') and result.content:
                # The server returns a stringified JSON/Dict
                response_text = result.content[0].text
                
                # Try to parse it as JSON for better formatting
                try:
                    import ast
                    data = ast.literal_eval(response_text)
                    
                    # Display Metadata
                    if "Metadata" in data:
                        meta = data.pop("Metadata")
                        col1, col2 = st.columns(2)
                        col1.metric("Ticker", meta.get("Symbol"))
                        col2.metric("Current Price", f"₹{meta.get('Price')}")
                    
                    # Display Indicators
                    st.json(data)
                    
                except:
                    # Fallback if it's just text
                    st.code(response_text, language="json")
            else:
                st.error("No content returned from server.")

with st.expander("Debug Info"):
    st.info(f"Server Script Path: {os.path.abspath(SERVER_SCRIPT)}")