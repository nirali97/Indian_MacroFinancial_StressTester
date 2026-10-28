"""Fetches a small snapshot of available market data using yfinance."""

from datetime import datetime, timezone
import pandas as pd

DEFAULT_TICKERS = {
    "NIFTY 50": "^NSEI", "NIFTY BANK": "^NSEBANK",
    "SBI": "SBIN.NS", "HDFC Bank": "HDFCBANK.NS", "ICICI Bank": "ICICIBANK.NS"
}

def fetch_market_snapshot(tickers=None, period="3mo"):
    """Get the latest available prices from Yahoo Finance (they may not be live)."""
    try:
        import yfinance as yf
    except ImportError as exc:
        raise RuntimeError("Install yfinance with: pip install yfinance") from exc
    result = []
    for name, ticker in (tickers or DEFAULT_TICKERS).items():
        try:
            hist = yf.Ticker(ticker).history(period=period, auto_adjust=True)
            if hist.empty or "Close" not in hist:
                result.append({"name":name,"ticker":ticker,"status":"unavailable"})
                continue
            close = hist["Close"].dropna()
            latest = float(close.iloc[-1])
            previous = float(close.iloc[-2]) if len(close) > 1 else latest
            result.append({
                "name":name, "ticker":ticker, "latest_close":latest,
                "daily_return_pct":((latest/previous)-1)*100 if previous else 0.0,
                "market_date":str(close.index[-1].date()),
                "retrieved_at_utc":datetime.now(timezone.utc).isoformat(),
                "status":"ok"
            })
        except Exception as exc:
            result.append({"name":name,"ticker":ticker,"status":"error","error":type(exc).__name__})
    return pd.DataFrame(result)
