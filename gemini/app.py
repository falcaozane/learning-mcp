import streamlit as st
import asyncio
import nest_asyncio
from mcp import ClientSession
from mcp.client.sse import sse_client
import httpx

# Patch asyncio to allow nested event loops in Streamlit
nest_asyncio.apply()

st.set_page_config(page_title="MCP Tool Console", page_icon="🎛️", layout="wide")

# --- 1. ASYNC HELPERS ---
# Streamlit runs synchronously, so we need these wrappers to talk to the async MCP SDK.

async def fetch_tools(server_url):
    """Connects to the server and fetches the list of available tools."""
    try:
        async with sse_client(server_url) as streams:
            read_stream, write_stream = streams
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.list_tools()
                return result.tools
    except Exception as e:
        return f"Error: {str(e)}"

async def run_tool(server_url, tool_name, arguments):
    """Connects to the server and executes a specific tool."""
    try:
        async with sse_client(server_url) as streams:
            read_stream, write_stream = streams
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments)
                return result
    except Exception as e:
        return f"Error: {str(e)}"

def run_async(coro):
    """Helper to run async code in Streamlit."""
    return asyncio.run(coro)

# --- 2. SIDEBAR CONFIGURATION ---
with st.sidebar:
    st.title("🔌 Connection")
    server_url = st.text_input("Server SSE URL", value="http://localhost:8000/mcp/sse")
    
    if st.button("Refresh Tools"):
        st.session_state.pop('tools', None)
        st.rerun()

    st.markdown("---")
    st.markdown("### Status")
    if 'tools' in st.session_state:
        st.success(f"Connected to {len(st.session_state['tools'])} tools")
    else:
        st.warning("Not connected")

# --- 3. MAIN APPLICATION ---
st.title("🎛️ MCP Client Dashboard")
st.markdown(
    """
    This dashboard acts as a manual **Model Context Protocol** client. 
    It connects to your FastAPI server, discovers tools, and lets you execute them without an AI.
    """
)

# A. Fetch Tools if not already loaded
if 'tools' not in st.session_state:
    with st.spinner(f"Connecting to {server_url}..."):
        tools_or_error = run_async(fetch_tools(server_url))
        
        if isinstance(tools_or_error, str):
            st.error(f"Failed to connect: {tools_or_error}")
            st.stop()
        else:
            st.session_state['tools'] = tools_or_error
            st.rerun()

# B. Tool Selector
tools = st.session_state['tools']
tool_names = [t.name for t in tools]

selected_tool_name = st.selectbox("Select Tool", tool_names)

# Find the full tool object
selected_tool = next((t for t in tools if t.name == selected_tool_name), None)

if selected_tool:
    st.markdown(f"**Description:** *{selected_tool.description}*")
    st.markdown("---")

    # C. Dynamic Form Generation
    # We parse the JSON Schema of the tool to create Streamlit widgets automatically.
    with st.form("tool_execution_form"):
        st.subheader("📝 Input Arguments")
        
        args = {}
        properties = selected_tool.inputSchema.get('properties', {})
        
        # Create columns for a cleaner layout
        cols = st.columns(2)
        idx = 0
        
        for arg_name, arg_schema in properties.items():
            col = cols[idx % 2]
            idx += 1
            
            arg_type = arg_schema.get('type', 'string')
            title = arg_schema.get('title', arg_name)
            
            with col:
                if arg_type == 'integer' or arg_type == 'number':
                    args[arg_name] = st.number_input(
                        label=title,
                        value=0
                    )
                else:
                    args[arg_name] = st.text_input(
                        label=title,
                        value=""
                    )

        submitted = st.form_submit_button("🚀 Execute Tool")

    # D. Execution & Results
    if submitted:
        with st.spinner("Running tool on server..."):
            result = run_async(run_tool(server_url, selected_tool_name, args))
            
            st.markdown("### 📄 Result")
            if isinstance(result, str) and result.startswith("Error"):
                st.error(result)
            else:
                # MCP returns a list of content blocks (Text or Image)
                for content in result.content:
                    if content.type == 'text':
                        st.info(content.text)
                        # Try to parse as JSON for pretty printing if possible
                        try:
                            import json
                            json_data = json.loads(content.text)
                            st.json(json_data)
                        except:
                            pass
                    elif content.type == 'image':
                        st.image(content.data, caption="Tool Output Image")