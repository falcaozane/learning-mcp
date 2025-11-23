import yfinance as yf
import pandas as pd

def format_ticker(symbol: str) -> str:
    """
    Standardizes ticker symbols for Indian Markets.
    """
    symbol = symbol.upper().strip()
    # Check if suffix already exists or if it's a known index like ^NSEI
    if "." in symbol or "^" in symbol:
        return symbol
    # Default to NSE
    return f"{symbol}.NS"

def fetch_market_data(symbol: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
    """
    Fetches historical data.
    """
    ticker = format_ticker(symbol)
    df = yf.Ticker(ticker).history(period=period, interval=interval)
    
    if df.empty:
        raise ValueError(f"No data found for {ticker}")
    
    return df