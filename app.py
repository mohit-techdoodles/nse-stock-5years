"""
Streamlit app: fetch NSE stock OHLC data for a chosen date range and download as CSV.
Run locally:  streamlit run app.py
"""

import time
import random
import calendar
from datetime import date, timedelta

import pandas as pd
import requests
import streamlit as st
import yfinance as yf

st.set_page_config(page_title="NSE Stock Data Fetcher", page_icon="📈", layout="centered")

MIN_YEAR = 1990

# A browser-like session helps avoid Yahoo Finance treating requests from
# shared cloud-host IPs (e.g. Streamlit Cloud) as bot traffic.
_session = requests.Session()
_session.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
})


def date_selector(label, default_date, key_prefix):
    """Year/Month/Day dropdowns — avoids the native date picker's slow decade-by-decade
    year scrolling when the allowed range spans many decades."""
    years = list(range(date.today().year, MIN_YEAR - 1, -1))  # most recent first
    months = list(range(1, 13))

    c1, c2, c3 = st.columns(3)
    with c1:
        year = st.selectbox(
            f"{label} — Year", years,
            index=years.index(default_date.year),
            key=f"{key_prefix}_year",
        )
    with c2:
        month = st.selectbox(
            f"{label} — Month", months,
            index=default_date.month - 1,
            format_func=lambda m: date(2000, m, 1).strftime("%b"),
            key=f"{key_prefix}_month",
        )
    with c3:
        max_day = calendar.monthrange(year, month)[1]
        default_day = min(default_date.day, max_day)
        day = st.selectbox(
            f"{label} — Day", list(range(1, max_day + 1)),
            index=default_day - 1,
            key=f"{key_prefix}_day",
        )
    return date(year, month, day)


def fetch_with_retry(ticker, start, end, retries=4, base_delay=5):
    """Fetch data with retry + exponential backoff.
    Longer, increasing delays help when Yahoo is soft-rate-limiting
    (vs. a hard IP block, which no amount of retrying fixes)."""
    for attempt in range(1, retries + 1):
        try:
            df = yf.download(
                ticker,
                start=start,
                end=end,
                interval="1d",
                auto_adjust=True,
                progress=False,
                session=_session,
            )
            if not df.empty:
                return df, None
        except Exception as e:
            last_error = str(e)
        else:
            last_error = "Empty response"
        if attempt < retries:
            sleep_time = base_delay * (2 ** (attempt - 1)) + random.uniform(0, 2)
            time.sleep(sleep_time)
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
    symbol = st.text_input(
        "Stock symbol (NSE)",
        value="RELIANCE",
        help="e.g. RELIANCE, TCS, IDEA, INFY — without .NS. For indices, use the full Yahoo symbol, e.g. ^NSEI for NIFTY 50 or ^BSESN for SENSEX.",
    ).strip().upper()

with col2:
    st.write("")  # spacing

default_start = date.today() - timedelta(days=5 * 365)
default_end = date.today()

st.write("Start date")
start_date = date_selector("Start", default_start, "start")

st.write("End date")
end_date = date_selector("End", default_end, "end")

generate = st.button("Generate", type="primary", use_container_width=True)

if generate:
    if not symbol:
        st.error("Please enter a stock symbol.")
        st.stop()

    if start_date >= end_date:
        st.error("Start date must be before end date.")
        st.stop()

    # Indices (e.g. ^NSEI for NIFTY 50, ^BSESN for SENSEX) already have the right format
    # on Yahoo Finance and should NOT get .NS appended — only plain stock symbols do.
    ticker = symbol if symbol.startswith("^") else f"{symbol}.NS"

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