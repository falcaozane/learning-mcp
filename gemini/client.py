import asyncio
import httpx
from mcp import ClientSession
from mcp.client.sse import sse_client

# The URL where your FastAPI app creates the MCP stream
SERVER_URL = "http://localhost:8000/mcp/sse"

async def run_client():
    print(f"🔌 Connecting to MCP Server at {SERVER_URL}...")

    # 1. Connect via Server-Sent Events (SSE)
    # The server keeps this connection open to push updates/events to us.
    async with sse_client(SERVER_URL) as streams:
        read_stream, write_stream = streams

        # 2. Initialize the Session
        # This performs the MCP Handshake (Client sends "Hello", Server sends "Hello")
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            print("✅ Connected and Initialized!")

            # 3. List Available Tools
            # We ask the server: "What functions can I call?"
            tools_list = await session.list_tools()
            print(f"\n🛠️  Found {len(tools_list.tools)} tool(s):")
            for tool in tools_list.tools:
                print(f"   - Name: {tool.name}")
                print(f"     Description: {tool.description}")
            
            # 4. Call a Tool
            # In a real AI agent, the LLM decides to do this. 
            # Here, we are hardcoding the call to test the connection.
            tool_name = "get_compound_interest_projection"
            arguments = {
                "principal": 1000, 
                "rate": 5, 
                "years": 10
            }
            
            print(f"\n🚀 Calling tool '{tool_name}' with args: {arguments}...")
            
            result = await session.call_tool(tool_name, arguments)
            
            # 5. Display Result
            # The result comes back as a list of content blocks (usually text)
            print("\n📄 Result from Server:")
            for content in result.content:
                if content.type == "text":
                    print(f"   {content.text}")

if __name__ == "__main__":
    # Run the async loop
    try:
        asyncio.run(run_client())
    except httpx.ConnectError:
        print("❌ Error: Could not connect. Is 'server.py' running?")
    except Exception as e:
        print(f"❌ Error: {e}")