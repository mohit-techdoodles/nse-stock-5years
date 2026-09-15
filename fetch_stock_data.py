"""
Fetch 5 years of daily OHLC data for a single NSE stock and save to CSV.
Usage: python fetch_single_stock.py [SYMBOL]
Example: python fetch_single_stock.py RELIANCE
"""

import sys
import time
import pandas as pd
import yfinance as yf


def fetch_with_retry(ticker, period="5y", interval="1d", retries=3, delay=5):
    """Fetch data with retry on failure/empty response."""
    for attempt in range(1, retries + 1):
        try:
            df = yf.download(
                ticker,
                period=period,
                interval=interval,
                auto_adjust=True,   # split/dividend adjusted -> accurate for historical analysis
                progress=False,
            )
            if not df.empty:
                return df
            print(f"Attempt {attempt}: empty response for {ticker}")
        except Exception as e:
            print(f"Attempt {attempt} failed for {ticker}: {e}")
        if attempt < retries:
            time.sleep(delay)
    return pd.DataFrame()


def validate(df, symbol):
    """Run sanity checks on the fetched data. Returns list of warnings."""
    warnings = []

    if df.empty:
        warnings.append("DataFrame is empty.")
        return warnings

    if df.isnull().any().any():
        warnings.append(f"Found {df.isnull().sum().sum()} null values.")

    bad_rows = df[
        (df["High"] < df["Low"]) |
        (df["High"] < df["Open"]) |
        (df["Open"] < df["Low"]) |
        (df["Close"] > df["High"]) |
        (df["Close"] < df["Low"])
    ]

    if not bad_rows.empty:
        warnings.append(f"Found {len(bad_rows)} rows with inconsistent High/Low/Open values.")

    if df["Date"].duplicated().any():
        warnings.append(f"Found {df['Date'].duplicated().sum()} duplicate dates.")

    expected_min_rows = 1150  # ~230 trading days/year * 5, with buffer
    if len(df) < expected_min_rows:
        warnings.append(
            f"Only {len(df)} rows fetched — expected ~1200+. Data may be incomplete."
        )

    return warnings


def main():
    symbol = sys.argv[1] if len(sys.argv) > 1 else "IDEA"
    ticker = f"{symbol}.NS"

    print(f"Fetching 5y daily data for {ticker}...")
    raw = fetch_with_retry(ticker)

    if raw.empty:
        print(f"FAILED: could not retrieve data for {ticker} after retries.")
        sys.exit(1)

    # yfinance may return MultiIndex columns even for a single ticker in some versions
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)

    df = raw[["Open", "High", "Low", "Close"]].dropna().copy()
    df.reset_index(inplace=True)
    df["Date"] = df["Date"].dt.date

    warnings = validate(df, symbol)
    if warnings:
        print("\nValidation warnings:")
        for w in warnings:
            print(f"  - {w}")
    else:
        print("\nValidation passed: no issues found.")

    out_file = f"{symbol}_5yr_daily.csv"
    df.to_csv(out_file, index=False)
    print(f"\nSaved {len(df)} rows to {out_file}")
    print(f"Date range: {df['Date'].min()} to {df['Date'].max()}")


if __name__ == "__main__":
    main()