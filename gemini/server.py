import uvicorn
import json
from fastapi import FastAPI
from fastmcp import FastMCP
from pydantic import BaseModel

# --- 1. SHARED BUSINESS LOGIC ---
def calculate_compound_interest(principal: float, rate: float, years: int) -> dict:
    # Generate year-by-year growth for the chart
    growth_data = []
    current_amount = principal
    for year in range(years + 1):
        growth_data.append({"year": year, "amount": round(current_amount, 2)})
        current_amount = current_amount * (1 + (rate / 100))

    final_amount = growth_data[-1]["amount"]
    
    return {
        "principal": principal,
        "rate_percent": rate,
        "years": years,
        "final_amount": final_amount,
        "profit": round(final_amount - principal, 2),
        "growth_chart": growth_data # Added for visualization
    }

# --- 2. SETUP FASTAPI ---
app = FastAPI(title="Hybrid Finance Server")

class InterestRequest(BaseModel):
    principal: float
    rate: float
    years: int

@app.post("/calculate/interest")
def api_calculate_interest(data: InterestRequest):
    return calculate_compound_interest(data.principal, data.rate, data.years)

@app.get("/")
def health_check():
    return {"status": "online", "mode": "hybrid"}

# --- 3. SETUP FASTMCP ---
mcp = FastMCP("Finance Tools")

@mcp.tool()
def get_compound_interest_projection(principal: float, rate: float, years: int) -> str:
    """
    Calculates compound interest and returns structured JSON data including 
    year-over-year growth.
    """
    result = calculate_compound_interest(principal, rate, years)
    # Return JSON string so the client can parse it into a chart
    return json.dumps(result)

# --- 4. MOUNT ---
app.mount("/mcp", mcp.sse_app())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)