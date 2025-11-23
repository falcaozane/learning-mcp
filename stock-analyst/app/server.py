from fastmcp import FastMCP
import pandas as pd
import inspect

# Relative imports from within the app package
from . import technical_indicators as ta
from . import data_engine

# Initialize Server
mcp = FastMCP("IndianStockAnalyst")

@mcp.tool()
def list_available_indicators() -> list[str]:
    """Returns a list of all technical indicators capable of being calculated."""
    return [name for name, obj in inspect.getmembers(ta) 
            if inspect.isfunction(obj) and not name.startswith("_")]

@mcp.tool()
def calculate_technicals(symbol: str, indicators: list[str], period: str = "1y") -> str:
    """
    Calculates specific technical indicators for an Indian Stock.
    
    Args:
        symbol: Ticker (e.g., RELIANCE, TCS, INFY).
        indicators: List of function names (e.g., ["RSI", "MACD", "BB"]).
        period: Timeframe (default "1y").
    """
    try:
        # 1. Get Data
        df = data_engine.fetch_market_data(symbol, period)
        
        # 2. Run Calculations
        results = {}
        latest_date = df.index[-1].strftime('%Y-%m-%d')
        results['Metadata'] = {'Symbol': symbol.upper(), 'Date': latest_date, 'Price': round(df['Close'].iloc[-1], 2)}
        
        for ind_name in indicators:
            if hasattr(ta, ind_name):
                func = getattr(ta, ind_name)
                try:
                    # Execute math
                    calc = func(df)
                    
                    # Format output (Get last value)
                    if isinstance(calc, pd.Series):
                        results[ind_name] = round(calc.iloc[-1], 2)
                    elif isinstance(calc, pd.DataFrame):
                        # Convert last row to dict and round values
                        row = calc.iloc[-1].to_dict()
                        results[ind_name] = {k: round(v, 2) for k, v in row.items()}
                        
                except Exception as e:
                    results[ind_name] = f"Math Error: {str(e)}"
            else:
                results[ind_name] = "Indicator not found"

        return str(results)

    except Exception as e:
        return f"Error: {str(e)}"
    

@mcp.tool()
def get_historical_technicals(symbol: str, indicators: list[str], period: str = "1y") -> str:
    """
    Returns historical data for plotting.
    Output is a JSON string containing dates, closing price, and indicator values over time.
    """
    import json
    try:
        # 1. Fetch Data
        df = data_engine.fetch_market_data(symbol, period)
        
        # 2. Calculate Indicators
        # We run the calculations which append columns to 'df'
        response_data = {
            "dates": df.index.strftime('%Y-%m-%d').tolist(),
            "Close": df['Close'].round(2).tolist(),
            "indicators": {}
        }

        for ind_name in indicators:
            if hasattr(ta, ind_name):
                func = getattr(ta, ind_name)
                try:
                    result = func(df)
                    
                    # Handle Series vs DataFrame return types
                    if isinstance(result, pd.Series):
                        # Replace NaN with None for valid JSON
                        response_data["indicators"][ind_name] = result.where(pd.notnull(result), None).tolist()
                    
                    elif isinstance(result, pd.DataFrame):
                        # For multi-line indicators like MACD or BB
                        for col in result.columns:
                            key_name = f"{ind_name}_{col}"
                            response_data["indicators"][key_name] = result[col].where(pd.notnull(result[col]), None).tolist()
                            
                except Exception as e:
                    print(f"Error calcuating {ind_name}: {e}")
        
        return json.dumps(response_data)

    except Exception as e:
        return json.dumps({"error": str(e)})