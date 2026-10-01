# NSE Stock Data Fetcher — User Guide

A simple web app to fetch historical daily OHLC(V) data for any NSE-listed stock
or major Indian market index, and download it as a CSV file.

---

## How to Use

1. **Enter a symbol** in the "Stock symbol (NSE)" box.
2. **Choose a Start date and End date** using the Year / Month / Day dropdowns.
   Defaults to the last 5 years if left unchanged.
3. Click **Generate**.
4. Review the preview table and any validation warnings.
5. Click **Download CSV** to save the file.

---

## What to Type in the Symbol Box

The app automatically formats your input differently depending on whether
it's a regular stock or a market index:

| You type | App sends to Yahoo Finance | Use for |
|---|---|---|
| `RELIANCE` | `RELIANCE.NS` | Individual NSE-listed stocks |
| `^NSEI` | `^NSEI` (unchanged) | Market indices (symbol starts with `^`) |

**Rule of thumb:** plain stock symbols get `.NS` added automatically.
Anything starting with `^` is treated as an index and sent exactly as typed.

---

## NSE Stock Symbols (examples)

Use the plain trading symbol, no suffix needed:

| Company | Symbol to type |
|---|---|
| Reliance Industries | `RELIANCE` |
| Tata Consultancy Services | `TCS` |
| Infosys | `INFY` |
| HDFC Bank | `HDFCBANK` |
| ICICI Bank | `ICICIBANK` |
| Vodafone Idea | `IDEA` |
| State Bank of India | `SBIN` |
| ITC | `ITC` |
| Larsen & Toubro | `LT` |
| Bharti Airtel | `BHARTIARTL` |

> Tip: You can find any company's exact NSE symbol on the
> [NSE India website](https://www.nseindia.com) or by searching
> "`<company name>` NSE symbol".

---

## NIFTY 50 and Other Major Indices

Indices use a `^`-prefixed symbol on Yahoo Finance — type these exactly as shown:

| Index | Symbol to type |
|---|---|
| NIFTY 50 | `^NSEI` |
| NIFTY Bank | `^NSEBANK` |
| NIFTY Next 50 | `^NSMIDCP` |
| SENSEX (BSE) | `^BSESN` |
| NIFTY IT | `^CNXIT` |
| NIFTY Midcap 100 | `^NSEMDCP50` |

> If an index symbol returns no data, double-check the exact ticker on
> [Yahoo Finance](https://finance.yahoo.com) by searching the index name —
> Yahoo occasionally updates or varies these symbols.

---

## Choosing a Date Range

- Use the **Year / Month / Day dropdowns** under Start date and End date.
- Earliest selectable year is **1990** (NSE/NIFTY data on Yahoo Finance
  typically starts mid-1990s onward; individual stocks only have data
  from their actual listing date).
- Start date must be **before** End date, or the app will show an error.
- Day options automatically adjust to the correct number of days for the
  selected month and year (e.g. no "Feb 30").

---

## Understanding the Output

The downloaded CSV contains:

| Column | Description |
|---|---|
| Date | Trading date |
| Open | Opening price |
| High | Highest price during the day |
| Low | Lowest price during the day |
| Close | Closing price (split/dividend-adjusted) |
| Volume | Shares traded that day (if available) |

Prices are **adjusted** for stock splits and bonus issues, so historical
values stay consistent with current prices — this is what makes the data
suitable for long-term analysis or backtesting.

---

## Validation Checks (Automatic)

Every time you click Generate, the app automatically checks the fetched
data for:

- Missing (null) values
- Duplicate dates
- Logical inconsistencies (e.g. High lower than Low, Close outside the
  day's High-Low range)

If anything looks off, a warning box will appear above the data preview.
If everything passes, you'll see "Validation passed: no issues found."

---

## Troubleshooting

| Problem | Likely Cause | Fix |
|---|---|---|
| "Could not retrieve data" error | Invalid symbol, or no `.NS`/`^` needed where you added one | Double-check the symbol against the tables above |
| Very few rows returned | Stock listed recently / index history doesn't go back that far | Try a shorter, more recent date range |
| Data looks outdated | Yahoo Finance data has a slight delay intraday | Re-run later in the day after market close for final values |

---

## Quick Reference Card

```
Stock:        RELIANCE, TCS, INFY, HDFCBANK, IDEA, SBIN, ...  (no suffix)
NIFTY 50:     ^NSEI
NIFTY Bank:   ^NSEBANK
SENSEX:       ^BSESN
```
