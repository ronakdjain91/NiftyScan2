import streamlit as st
import yfinance as yf
import pandas as pd

# ----------- Helper Functions -----------

def compute_rsi(data, window=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def fundamentals_check(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        # Example fundamental filters
        pe_ok = info.get('trailingPE', None) and info['trailingPE'] < 30
        profit_ok = info.get('profitMargins', None) and info['profitMargins'] > 0
        debt_ok = info.get('debtToEquity', None) and info['debtToEquity'] < 100

        return pe_ok and profit_ok and debt_ok
    except:
        return False

def buy_sell_indicator(df, fundamentals_ok):
    if not fundamentals_ok:
        return "Sell"

    ma200 = df['Close'].rolling(window=200).mean()
    rsi = compute_rsi(df['Close'])
    latest_price = df['Close'].iloc[-1]
    latest_rsi = rsi.iloc[-1]

    if latest_price > ma200.iloc[-1] and 40 < latest_rsi < 60:
        return "Buy"
    else:
        return "Sell"

# ----------- Streamlit UI -----------

st.title("📈 Nifty Stock Scanner")

# Persistent ticker list
if "tickers" not in st.session_state:
    st.session_state.tickers = ["RELIANCE.NS", "TCS.NS", "INFY.NS"]

# Add new ticker
new_ticker = st.text_input("Add a new ticker (e.g. HDFCBANK.NS)")
if st.button("Add") and new_ticker:
    if new_ticker not in st.session_state.tickers:
        st.session_state.tickers.append(new_ticker)

# Remove tickers
remove_tickers = st.multiselect("Remove tickers", st.session_state.tickers)
if st.button("Remove Selected"):
    for t in remove_tickers:
        st.session_state.tickers.remove(t)

# Scan stocks
results = []
for ticker in st.session_state.tickers:
    try:
        df = yf.download(ticker, period="1y", interval="1d")
        fundamentals_ok = fundamentals_check(ticker)
        signal = buy_sell_indicator(df, fundamentals_ok)
        results.append({
            "Ticker": ticker,
            "Signal": signal,
            "TradingView": f"[View](https://www.tradingview.com/symbols/NSE-{ticker.replace('.NS','')}/)"
        })
    except:
        results.append({"Ticker": ticker, "Signal": "Error", "TradingView": "N/A"})

# Show results
df_results = pd.DataFrame(results)
st.dataframe(df_results, use_container_width=True)
