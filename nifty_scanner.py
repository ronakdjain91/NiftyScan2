# nifty_scanner_app.py

import yfinance as yf
import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime, timedelta

# -------- CONFIG --------
NIFTY50 = [
    "RELIANCE.NS","TCS.NS","HDFCBANK.NS","HDFC.NS","INFY.NS","ICICIBANK.NS","KOTAKBANK.NS",
    "HINDUNILVR.NS","SBIN.NS","LT.NS","AXISBANK.NS","ITC.NS","HCLTECH.NS","BHARTIARTL.NS",
    "ASIANPAINT.NS","MARUTI.NS","SUNPHARMA.NS","NESTLEIND.NS","TITAN.NS","ULTRACEMCO.NS",
    "POWERGRID.NS","ONGC.NS","NTPC.NS","INDUSINDBK.NS","BAJAJ-AUTO.NS","BAJFINANCE.NS",
    "BRITANNIA.NS","DIVISLAB.NS","EICHERMOT.NS","GRASIM.NS","HDFCLIFE.NS","IOC.NS","JSWSTEEL.NS",
    "WIPRO.NS","TATASTEEL.NS","COALINDIA.NS","SBILIFE.NS","BPCL.NS","ADANIENT.NS",
    "TECHM.NS","M&M.NS","CIPLA.NS","HEROMOTOCO.NS","INDIGO.NS","SHREECEM.NS","TATAMOTORS.NS",
    "UPL.NS","HINDALCO.NS"
]
NIFTY50 = list(dict.fromkeys(NIFTY50))
PERIOD = "1y"
INTERVAL = "1d"

# -------- HELPERS --------
def sma(series, window):
    return series.rolling(window=window, min_periods=1).mean()

def rsi(series, window=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -1 * delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/window, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/window, adjust=False).mean()
    rs = avg_gain / (avg_loss.replace(0, np.nan))
    rsi_val = 100 - (100 / (1 + rs))
    return rsi_val.fillna(50)

def macd(series, fast=12, slow=26, signal=9):
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    hist = macd_line - signal_line
    return macd_line, signal_line, hist

def fundamentals_score(ticker_obj):
    info = ticker_obj.info if hasattr(ticker_obj, "info") else {}
    score = 0
    max_score = 5

    pe = info.get("trailingPE") or info.get("forwardPE")
    if pe and pe > 0:
        if pe < 15: score += 2
        elif pe < 25: score += 1

    dte = info.get("debtToEquity")
    if dte is not None:
        if dte < 50: score += 1
        elif dte < 100: score += 0.5

    roe = info.get("returnOnEquity") or info.get("returnOnAssets")
    if roe is not None:
        if roe >= 0.15: score += 1
        elif roe > 0.08: score += 0.5

    try:
        fin = ticker_obj.quarterly_financials
        rev_row = None
        for candidate in ["Total Revenue", "TotalRevenue", "totalRevenue", "Revenue"]:
            if candidate in fin.index:
                rev_row = fin.loc[candidate]
                break
        if rev_row is None and not fin.empty:
            rev_row = fin.iloc[0]
        rev_vals = rev_row.dropna().astype(float)
        if len(rev_vals) >= 3:
            growth = (rev_vals.iloc[0] - rev_vals.iloc[-1]) / (abs(rev_vals.iloc[-1]) + 1e-6)
            if growth > 0.03:
                score += 1
    except Exception:
        pass

    return score, max_score, {"pe": pe, "de_ratio": dte, "roe": roe}

def technicals_score(df):
    close = df["Close"]
    s50 = sma(close, 50)
    s200 = sma(close, 200)
    rsi_val = rsi(close).iloc[-1]
    macd_line, signal_line, hist = macd(close)
    macd_hist = hist.iloc[-1]

    score = 0
    max_score = 5
    price = close.iloc[-1]

    if price > s200.iloc[-1]:
        score += 2
    elif price > s50.iloc[-1]:
        score += 1

    if s50.iloc[-1] > s200.iloc[-1]:
        score += 1

    if 30 < rsi_val < 70:
        score += 1
    elif rsi_val < 30:
        score += 0.5

    if macd_hist > 0:
        score += 0.5

    return score, max_score, {
        "price": price,
        "s50": s50.iloc[-1],
        "s200": s200.iloc[-1],
        "rsi": float(rsi_val),
        "macd_hist": float(macd_hist)
    }

def recommend(fund_score, fund_max, tech_score, tech_max, fund_threshold=2.5):
    fund_pct = fund_score / fund_max
    tech_pct = tech_score / tech_max
    final_score = 0.6 * fund_pct + 0.4 * tech_pct

    if fund_score < fund_threshold:
        rec = "Sell"
    else:
        if final_score >= 0.7:
            rec = "Buy"
        elif final_score >= 0.45:
            rec = "Hold"
        else:
            rec = "Sell"

    return rec, final_score

def scan_universe(ticker_list):
    results = []
    for sym in ticker_list:
        try:
            tk = yf.Ticker(sym)
            hist = tk.history(period=PERIOD, interval=INTERVAL, actions=False)
            if hist.empty:
                continue
            fscore, fmax, fmeta = fundamentals_score(tk)
            tscore, tmax, tmeta = technicals_score(hist)
            rec, final_score = recommend(fscore, fmax, tscore, tmax)
            tv_symbol = sym.replace(".NS", "")
            tradingview_link = f"https://in.tradingview.com/symbols/NSE:{tv_symbol}/"
            results.append({
                "Symbol": sym,
                "Price": round(tmeta["price"], 2),
                "Fundamental Score": fscore,
                "Technical Score": tscore,
                "Final Score": round(final_score, 3),
                "Recommendation": rec,
                "TradingView": f'<a href="{tradingview_link}" target="_blank">View</a>'
            })
        except Exception:
            continue

    df = pd.DataFrame(results).sort_values(by="Final Score", ascending=False).reset_index(drop=True)
    return df

# -------- STREAMLIT UI --------
st.set_page_config(page_title="Nifty Stock Scanner", layout="wide")
st.title("📊 Nifty Stock Scanner (Midterm Investment)")

if st.button("Run Scan"):
    with st.spinner("Scanning Nifty stocks... This can take a few minutes."):
        df = scan_universe(NIFTY50)
    st.success("Scan Complete!")

    rec_filter = st.multiselect(
        "Filter by Recommendation",
        options=df["Recommendation"].unique(),
        default=df["Recommendation"].unique()
    )
    df_filtered = df[df["Recommendation"].isin(rec_filter)]

    # Render clickable links
    st.markdown(df_filtered.to_html(escape=False, index=False), unsafe_allow_html=True)

    # Download CSV
    csv = df_filtered.to_csv(index=False).encode("utf-8")
    st.download_button("Download CSV", csv, "nifty_scan_results.csv", "text/csv")
else:
    st.info("Click 'Run Scan' to start analysis.")
