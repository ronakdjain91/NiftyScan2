import streamlit as st
import yfinance as yf
import pandas as pd
import ta

# -----------------------------------
# Default Tickers for Nifty indices
# -----------------------------------
NIFTY_50 = ["RELIANCE", "TCS", "HDFCBANK", "ICICIBANK", "INFY", "HINDUNILVR", "ITC", "KOTAKBANK", "LT", "SBIN"]  # Add all 50
NIFTY_MIDCAP_50 = ["AUROPHARMA", "BHEL", "BANKBARODA"]  # Add all 50
NIFTY_SMALLCAP_50 = ["ADANIPOWER", "IIFL", "RBLBANK"]  # Add all 50

DEFAULT_TICKERS = list(set(NIFTY_50 + NIFTY_MIDCAP_50 + NIFTY_SMALLCAP_50))

# -----------------------------------
# Helper to fetch data
# -----------------------------------
def get_stock_data(ticker):
    try:
        df = yf.download(f"{ticker}.NS", period="6mo", interval="1d", progress=False)
        if df.empty:
            return "error"
        df["RSI"] = ta.momentum.RSIIndicator(df["Close"]).rsi()
        macd = ta.trend.MACD(df["Close"])
        df["MACD"] = macd.macd()
        df["Signal"] = macd.macd_signal()
        return df
    except Exception:
        return "error"

# -----------------------------------
# Buy/Sell Indicator
# -----------------------------------
def buy_sell_indicator(df):
    if isinstance(df, str) and df == "error":
        return "Error"

    latest_rsi = df["RSI"].iloc[-1]
    macd_val = df["MACD"].iloc[-1]
    signal_val = df["Signal"].iloc[-1]

    if latest_rsi < 40 and macd_val > signal_val:
        return "Buy"
    elif latest_rsi > 60 and macd_val < signal_val:
        return "Sell"
    else:
        return "Hold"

# -----------------------------------
# Streamlit UI
# -----------------------------------
st.set_page_config(layout="wide")
st.title("📊 Nifty Stock Scanner")

# Filters
index_filter = st.selectbox("Select Index", ["All", "Nifty 50", "Nifty Midcap 50", "Nifty Smallcap 50"])
industry_filter = st.text_input("Filter by Industry (optional)")

# Ticker input
tickers = st.multiselect("Select Tickers", DEFAULT_TICKERS, default=DEFAULT_TICKERS)

# Apply index filter
if index_filter == "Nifty 50":
    tickers = [t for t in tickers if t in NIFTY_50]
elif index_filter == "Nifty Midcap 50":
    tickers = [t for t in tickers if t in NIFTY_MIDCAP_50]
elif index_filter == "Nifty Smallcap 50":
    tickers = [t for t in tickers if t in NIFTY_SMALLCAP_50]

# Fetch data
data_list = []
for t in tickers:
    df = get_stock_data(t)
    if df == "error":
        data_list.append({"Symbol": t, "Overall Rating": "-", "Signal": "Error fetching data from yfinance"})
    else:
        signal = buy_sell_indicator(df)
        overall_rating = "Strong" if signal == "Buy" else "Weak" if signal == "Sell" else "Neutral"
        data_list.append({
            "Symbol": t,
            "Overall Rating": overall_rating,
            "Signal": signal
        })

# Create DataFrame
df_display = pd.DataFrame(data_list)

# Add TradingView clickable link
df_display["TradingView"] = df_display["Symbol"].apply(
    lambda x: f'<a href="https://in.tradingview.com/symbols/NSE-{x}/" target="_blank">Chart</a>'
)

# Apply industry filter (dummy example - you'd need industry mapping)
if industry_filter:
    df_display = df_display[df_display["Symbol"].str.contains(industry_filter, case=False)]

# Show table
st.markdown(df_display.to_html(escape=False, index=False), unsafe_allow_html=True)

# CSV download
csv = df_display.to_csv(index=False).encode("utf-8")
st.download_button("Download CSV", csv, "nifty_scan.csv", "text/csv")
