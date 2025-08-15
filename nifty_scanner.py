import streamlit as st
import yfinance as yf
import pandas as pd

# ----------- Helper Functions -----------
def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def compute_macd(series, short_window=12, long_window=26, signal_window=9):
    short_ema = series.ewm(span=short_window, adjust=False).mean()
    long_ema = series.ewm(span=long_window, adjust=False).mean()
    macd = short_ema - long_ema
    signal = macd.ewm(span=signal_window, adjust=False).mean()
    return macd, signal

def check_fundamentals(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
    try:
        pe_ratio = info.get("trailingPE", None)
        debt_to_equity = info.get("debtToEquity", None)
        roe = info.get("returnOnEquity", None)
        
        if pe_ratio and pe_ratio < 25 and debt_to_equity and debt_to_equity < 100 and roe and roe > 0.10:
            return True
        else:
            return False
    except:
        return False

def buy_sell_indicator(df, fundamentals_ok):
    if not fundamentals_ok:
        return "Sell"

    ma200 = df['Close'].rolling(window=200).mean()
    rsi = compute_rsi(df['Close'])
    macd, signal = compute_macd(df['Close'])

    latest_price = df['Close'].iloc[-1]
    latest_rsi = rsi.iloc[-1]
    latest_macd = macd.iloc[-1]
    latest_signal = signal.iloc[-1]

    price_condition = latest_price > ma200.iloc[-1]
    rsi_condition = 40 < latest_rsi < 60
    macd_condition = latest_macd > latest_signal

    if price_condition and rsi_condition and macd_condition:
        return "Buy"
    else:
        return "Sell"

# ----------- Streamlit UI -----------
st.title("Nifty Stocks Scanner - Midterm Investment")
st.write("Fundamentals first, then technicals (MA200, RSI, MACD) for Buy/Sell signals")

# Manage Tickers
default_tickers = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS"]
tickers = st.text_area("Enter Nifty tickers (comma-separated):", ", ".join(default_tickers))
tickers = [t.strip() for t in tickers.split(",") if t.strip()]

# Date range
period = "1y"

results = []
for ticker in tickers:
    df = yf.download(ticker, period=period, interval="1d")
    if df.empty:
        continue

    fundamentals_ok = check_fundamentals(ticker)
    signal = buy_sell_indicator(df, fundamentals_ok)
    tradingview_link = f"https://www.tradingview.com/chart/?symbol={ticker}"

    results.append({
        "Ticker": ticker,
        "Signal": signal,
        "TradingView": f"[Open Chart]({tradingview_link})"
    })

# Display results
if results:
    st.markdown("### Results")
    df_results = pd.DataFrame(results)
    st.write(df_results.to_markdown(index=False), unsafe_allow_html=True)
