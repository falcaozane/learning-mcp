# fastapi_with_mcp_mount.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastmcp import FastMCP

# FastAPI part
class Item(BaseModel):
    name: str
    price: float

class ItemResponse(Item):
    id: int

api = FastAPI()

items = {}
next_id = 1

@api.post("/items", response_model=ItemResponse, operation_id="create_item")
def create_item(item: Item):
    global next_id
    item_resp = ItemResponse(id=next_id, **item.dict())
    items[next_id] = item_resp
    next_id += 1
    return item_resp

@api.get("/items/{item_id}", response_model=ItemResponse, operation_id="get_item")
def get_item(item_id: int):
    if item_id not in items:
        raise HTTPException(status_code=404, detail="Item not found")
    return items[item_id]

# FastMCP part
mcp = FastMCP("ItemMCP")

# Define tools manually or use from_fastapi
# Here, just reuse the FastAPI endpoints as tools
# Using from_fastapi is easier:
mcp = FastMCP.from_fastapi(app=api, name="ItemMCP")

# Create ASGI app for MCP, mounted under /mcp
mcp_app = mcp.http_app(path="/mcp")

# IMPORTANT: give the FastAPI app the lifespan from mcp_app so startup/shutdown are managed
app = FastAPI(lifespan=mcp_app.lifespan)

# Mount the MCP app
app.mount("/mcp", mcp_app)

# Also include the API routes
# (since `api` already has routes, you can add them to main `app`)
for route in api.routes:
    app.router.routes.append(route)

# Now `app` serves:
# - API: GET /items, POST /items, etc.
# - MCP: under /mcp

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
