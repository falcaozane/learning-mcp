import asyncio
from fastmcp import Client

async def perform_item_ops():
    # Point to correct MCP URL (server is running on port 8001)
    client = Client("http://127.0.0.1:8001")

    async with client:
        # Optional — explicitly initialize
        await client.initialize(timeout=10.0)

        # List available tools
        tools = await client.list_tools()
        print("Tools:", [t.name for t in tools])

        # Depending on how FastMCP names tools, check names:
        # e.g., "create_item_items_post" or similar
        # Call create_item
        res = await client.call_tool("create_item_items_post", {
            "name": "MyItem",
            "price": 99.99
        })
        print("Create:", res.data)

        created = res.data
        item_id = created["id"]

        # Call get_item
        res2 = await client.call_tool("get_item_items__item_id__get", {
            "item_id": item_id
        })
        print("Get:", res2.data)

if __name__ == "__main__":
    asyncio.run(perform_item_ops())
