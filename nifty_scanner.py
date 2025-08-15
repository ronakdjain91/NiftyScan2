import streamlit as st
import pandas as pd
import yfinance as yf
import datetime
import numpy as np

# -------------------- CONFIG --------------------
st.set_page_config(page_title="Nifty Scanner", layout="wide")

# Default ticker lists
nifty_50 = ["RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS"]  # Add all Nifty 50
nifty_midcap_50 = ["ABB.NS","ALKEM.NS","APLAPOLLO.NS"]  # Add all Midcap 50
nifty_smallcap_50 = ["ACE.NS","APLLTD.NS","BALAMINES.NS"]  # Add all Smallcap 50

# Merge all
all_tickers = list(set(nifty_50 + nifty_midcap_50 + nifty_smallcap_50))

# -------------------- FUNCTIONS --------------------
def fetch_data(ticker):
    try:
        data = yf.download(ticker, period="1y", interval="1d")
        if data.empty:
            return None
        return data
    except Exception:
        return "error"

def calculate_rsi(data, period=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_macd(data, short=12, long=26, signal=9):
    short_ema = data['Close'].ewm(span=short, adjust=False).mean()
    long_ema = data['Close'].ewm(span=long, adjust=False).mean()
    macd = short_ema - long_ema
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    return macd, signal_line

def buy_sell_indicator(data):
    rsi = calculate_rsi(data)
    macd, signal_line = calculate_macd(data)

    latest_rsi = rsi.iloc[-1]
    latest_macd = macd.iloc[-1]
    latest_signal = signal_line.iloc[-1]

    # Fundamentals placeholder
    fundamentals_ok = True  # In real app, fetch actual fundamentals

    # Conditions
    rsi_condition = 40 < latest_rsi < 60
    macd_condition = latest_macd > latest_signal
    rating = 0

    if fundamentals_ok:
        rating += 1
    if rsi_condition:
        rating += 1
    if macd_condition:
        rating += 1

    if rating == 3:
        return "BUY", rating
    elif rating == 2:
        return "HOLD", rating
    else:
        return "SELL", rating

# -------------------- UI --------------------
st.title("📊 Nifty Stock Scanner (Mid-Term)")

# Filters
index_filter = st.selectbox("Select Index", ["All", "Nifty 50", "Midcap 50", "Smallcap 50"])
industry_filter = st.text_input("Filter by Industry (optional)")

if index_filter == "Nifty 50":
    tickers = nifty_50
elif index_filter == "Midcap 50":
    tickers = nifty_midcap_50
elif index_filter == "Smallcap 50":
    tickers = nifty_smallcap_50
else:
    tickers = all_tickers

final_data = []

for ticker in tickers:
    data = fetch_data(ticker)
    if data == "error":
        st.warning(f"⚠ Error fetching data from yfinance for {ticker}")
        continue
    if data is None:
        continue

    signal, rating = buy_sell_indicator(data)
    industry = "Unknown"  # Placeholder — add real industry mapping

    if industry_filter and industry_filter.lower() not in industry.lower():
        continue

    final_data.append({
        "Ticker": ticker,
        "Signal": signal,
        "Rating": rating,
        "TradingView": f"[Chart](https://www.tradingview.com/symbols/{ticker.replace('.NS','')}/)",
        "Industry": industry
    })

if final_data:
    df = pd.DataFrame(final_data)
    st.dataframe(df, use_container_width=True)

    # CSV download
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(label="📥 Download CSV", data=csv, file_name="nifty_scan.csv", mime='text/csv')
else:
    st.error("No data found for the selected filters.")
