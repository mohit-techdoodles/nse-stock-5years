"""
Streamlit app: fetch NSE stock OHLC data for a chosen date range and download as CSV.
Run locally:  streamlit run app.py
"""

import time
from datetime import date, timedelta

import pandas as pd
import streamlit as st
import yfinance as yf

st.set_page_config(page_title="NSE Stock Data Fetcher", page_icon="📈", layout="centered")


def fetch_with_retry(ticker, start, end, retries=3, delay=3):
    """Fetch data with retry on failure/empty response."""
    for attempt in range(1, retries + 1):
        try:
            df = yf.download(
                ticker,
                start=start,
                end=end,
                interval="1d",
                auto_adjust=True,
                progress=False,
            )
            if not df.empty:
                return df, None
        except Exception as e:
            last_error = str(e)
        else:
            last_error = "Empty response"
        if attempt < retries:
            time.sleep(delay)
    return pd.DataFrame(), last_error


def validate(df):
    """Run sanity checks. Returns list of warning strings."""
    warnings = []
    if df.empty:
        warnings.append("DataFrame is empty.")
        return warnings

    if df.isnull().any().any():
        warnings.append(f"Found {int(df.isnull().sum().sum())} null values.")

    bad_rows = df[
        (df["High"] < df["Low"])
        | (df["High"] < df["Open"])
        | (df["Open"] < df["Low"])
        | (df["Close"] > df["High"])
        | (df["Close"] < df["Low"])
    ]
    if not bad_rows.empty:
        warnings.append(f"Found {len(bad_rows)} rows with inconsistent OHLC values.")

    if df["Date"].duplicated().any():
        warnings.append(f"Found {int(df['Date'].duplicated().sum())} duplicate dates.")

    return warnings


# ---------- UI ----------
st.title("📈 NSE Stock Data Fetcher")
st.caption("Fetch daily OHLC(V) data for any NSE-listed stock and download as CSV.")

col1, col2 = st.columns([1, 1])
with col1:
    symbol = st.text_input("Stock symbol (NSE)", value="RELIANCE", help="e.g. RELIANCE, TCS, IDEA, INFY — without .NS").strip().upper()

with col2:
    st.write("")  # spacing

default_start = date.today() - timedelta(days=5 * 365)
default_end = date.today()

date_range = st.date_input(
    "Date range",
    value=(default_start, default_end),
    min_value=date(1990, 1, 1),   # allow picking any year back to 1990
    max_value=date.today(),
)

generate = st.button("Generate", type="primary", use_container_width=True)

if generate:
    if not symbol:
        st.error("Please enter a stock symbol.")
        st.stop()

    if not isinstance(date_range, tuple) or len(date_range) != 2:
        st.error("Please select a full date range (start and end date).")
        st.stop()

    start_date, end_date = date_range
    if start_date >= end_date:
        st.error("Start date must be before end date.")
        st.stop()

    ticker = f"{symbol}.NS"

    with st.spinner(f"Fetching data for {ticker}..."):
        # yfinance's `end` is exclusive, so add a day to include the end_date itself
        raw, error = fetch_with_retry(ticker, start_date, end_date + timedelta(days=1))

    if raw.empty:
        st.error(f"Could not retrieve data for **{ticker}**. It may be an invalid symbol or Yahoo Finance had no data for this range. ({error})")
        st.stop()

    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)

    keep_cols = [c for c in ["Open", "High", "Low", "Close", "Volume"] if c in raw.columns]
    df = raw[keep_cols].dropna().copy()
    df.reset_index(inplace=True)
    df["Date"] = df["Date"].dt.date

    warnings = validate(df)

    st.success(f"Fetched **{len(df)}** rows for **{ticker}** ({df['Date'].min()} to {df['Date'].max()})")

    if warnings:
        with st.expander("⚠️ Validation warnings", expanded=True):
            for w in warnings:
                st.write(f"- {w}")
    else:
        st.info("Validation passed: no issues found.")

    st.dataframe(df, use_container_width=True, height=300)

    csv_bytes = df.to_csv(index=False).encode("utf-8")
    file_name = f"{symbol}_{start_date}_{end_date}.csv"

    st.download_button(
        label="⬇️ Download CSV",
        data=csv_bytes,
        file_name=file_name,
        mime="text/csv",
        type="primary",
        use_container_width=True,
    )