import uvicorn
import json
import math
from fastapi import FastAPI
from fastmcp import FastMCP
from pydantic import BaseModel

# --- 1. SHARED BUSINESS LOGIC ---

def calculate_compound_interest(principal: float, rate: float, years: int) -> dict:
    growth_data = []
    current_amount = principal
    for year in range(years + 1):
        growth_data.append({"year": year, "amount": round(current_amount, 2)})
        current_amount = current_amount * (1 + (rate / 100))

    final_amount = growth_data[-1]["amount"]
    
    return {
        "tool": "interest",
        "principal": principal,
        "rate_percent": rate,
        "years": years,
        "final_amount": final_amount,
        "profit": round(final_amount - principal, 2),
        "growth_chart": growth_data 
    }

def calculate_mortgage(loan_amount: float, annual_rate: float, years: int) -> dict:
    monthly_rate = (annual_rate / 100) / 12
    num_payments = years * 12
    
    if monthly_rate == 0:
        monthly_payment = loan_amount / num_payments
    else:
        monthly_payment = loan_amount * (monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)
    
    total_payment = monthly_payment * num_payments
    total_interest = total_payment - loan_amount
    
    # Generate Amortization Schedule (Yearly snapshots for cleaner charts)
    schedule = []
    balance = loan_amount
    schedule.append({"year": 0, "balance": round(balance, 2)})
    
    for i in range(1, num_payments + 1):
        interest = balance * monthly_rate
        principal_part = monthly_payment - interest
        balance -= principal_part
        
        # Snapshot every 12 months (1 year)
        if i % 12 == 0:
            schedule.append({"year": i // 12, "balance": max(0, round(balance, 2))})
            
    return {
        "tool": "mortgage",
        "loan_amount": loan_amount,
        "monthly_payment": round(monthly_payment, 2),
        "total_interest": round(total_interest, 2),
        "total_payment": round(total_payment, 2),
        "amortization_schedule": schedule
    }

def calculate_time_to_goal(goal: float, monthly_contribution: float, annual_rate: float, current_savings: float = 0) -> dict:
    # Use logarithmic formula to find time
    # FV = P * ((1+r)^t - 1) / r  (Simplified annuity formula)
    # We iterate monthly to handle the mix of lump sum + contribution easiest
    
    months = 0
    balance = current_savings
    monthly_rate = (annual_rate / 100) / 12
    
    growth_data = [{"month": 0, "balance": balance}]
    
    while balance < goal and months < 1200: # Cap at 100 years to prevent infinite loops
        months += 1
        interest = balance * monthly_rate
        balance += interest + monthly_contribution
        
        if months % 6 == 0: # Snapshot every 6 months
             growth_data.append({"month": months, "balance": round(balance, 2)})

    years = round(months / 12, 1)
    
    return {
        "tool": "savings_goal",
        "goal_amount": goal,
        "years_needed": years,
        "total_months": months,
        "final_balance": round(balance, 2),
        "savings_chart": growth_data
    }

# --- 2. SETUP FASTAPI ---
app = FastAPI(title="Hybrid Finance Server")

# We can add REST endpoints for the new tools here if we wanted, 
# but for now we'll focus on the MCP tools.

@app.get("/")
def health_check():
    return {"status": "online", "mode": "hybrid", "tools": ["interest", "mortgage", "savings"]}

# --- 3. SETUP FASTMCP ---
mcp = FastMCP("Finance Tools")

@mcp.tool()
def get_compound_interest_projection(principal: float, rate: float, years: int) -> str:
    """Calculates compound interest growth over time."""
    result = calculate_compound_interest(principal, rate, years)
    return json.dumps(result)

@mcp.tool()
def calculate_monthly_mortgage(loan_amount: float, annual_rate: float, years: int) -> str:
    """
    Calculates monthly mortgage payments and amortization schedule.
    Use this for home loan or auto loan questions.
    """
    result = calculate_mortgage(loan_amount, annual_rate, years)
    return json.dumps(result)

@mcp.tool()
def calculate_savings_timeline(goal: float, monthly_contribution: float, annual_rate: float, current_savings: float = 0) -> str:
    """
    Calculates how long it will take to reach a savings goal.
    Returns the number of years and months required.
    """
    result = calculate_time_to_goal(goal, monthly_contribution, annual_rate, current_savings)
    return json.dumps(result)

# --- 4. MOUNT ---
app.mount("/mcp", mcp.sse_app())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)