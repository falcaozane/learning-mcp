import asyncio
from fastmcp import Client

client = Client("http://localhost:8000/mcp")

async def perform_arithmetic():
    async with client:
        # Addition
        result = await client.call_tool("add", {"a": 5, "b": 3})
        print(f"5 + 3 = {result.content[0].text}")
        
        # Subtraction
        result = await client.call_tool("subtract", {"a": 10, "b": 4})
        print(f"10 - 4 = {result.content[0].text}")
        
        # Multiplication
        result = await client.call_tool("multiply", {"a": 7, "b": 6})
        print(f"7 * 6 = {result.content[0].text}")
        
        # Division
        result = await client.call_tool("divide", {"a": 20, "b": 4})
        print(f"20 / 4 = {result.content[0].text}")
        
        # Power
        result = await client.call_tool("power", {"base": 2, "exponent": 8})
        print(f"2^8 = {result.content[0].text}")
        
        # Error handling example
        try:
            result = await client.call_tool("divide", {"a": 5, "b": 0})
            print(result.content[0].text)
        except Exception as e:
            print(f"Error dividing by zero: {e}")

asyncio.run(perform_arithmetic())