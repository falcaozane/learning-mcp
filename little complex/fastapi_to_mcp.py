# fastapi_to_mcp.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastmcp import FastMCP

# 1. Define a small FastAPI app
class Item(BaseModel):
    name: str
    price: float

class ItemResponse(Item):
    id: int

app = FastAPI()

# In-memory “DB”
items = {}
next_id = 1

@app.post("/items", response_model=ItemResponse, operation_id="create_item")
def create_item(item: Item):
    global next_id
    item_resp = ItemResponse(id=next_id, **item.dict())
    items[next_id] = item_resp
    next_id += 1
    return item_resp

@app.get("/items/{item_id}", response_model=ItemResponse, operation_id="get_item")
def get_item(item_id: int):
    if item_id not in items:
        raise HTTPException(status_code=404, detail="Item not found")
    return items[item_id]

# 2. Create an MCP server from the FastAPI app
mcp = FastMCP.from_fastapi(app=app, name="ItemMCP")

if __name__ == "__main__":
    # Run the MCP server via FastMCP’s HTTP transport
    mcp.run(transport="http",host="127.0.0.1", port=8001)
