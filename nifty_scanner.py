import streamlit as st
import pandas as pd
import yfinance as yf
import ta
from io import BytesIO

st.set_page_config(page_title="Nifty Scanner", layout="wide")

# --------------------- DEFAULT TICKERS ---------------------
nifty50 = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS"]
niftymidcap50 = ["MAXHEALTH.NS", "CUMMINSIND.NS", "TATAELXSI.NS"]
niftysmallcap50 = ["CENTURYTEX.NS", "GRAPHITE.NS", "NBCC.NS"]

default_tickers = list(set(nifty50 + niftymidcap50 + niftysmallcap50))

# --------------------- FETCH DATA ---------------------
def fetch_data(ticker):
    try:
        df = yf.download(ticker, period="6mo", interval="1d")
        if df.empty:
            return None
        df["RSI"] = ta.momentum.RSIIndicator(df["Close"]).rsi()
        macd = ta.trend.MACD(df["Close"])
        df["MACD"] = macd.macd()
        df["Signal"] = macd.macd_signal()
        return df
    except:
        return None

# --------------------- FUNDAMENTAL CHECK ---------------------
def fundamentals_ok(ticker):
    try:
        info = yf.Ticker(ticker).info
        pe = info.get("trailingPE", None)
        pb = info.get("priceToBook", None)
        return pe is not None and pb is not None and pe < 30 and pb < 5
    except:
        return False

# --------------------- BUY/SELL INDICATOR ---------------------
def buy_sell_indicator(df, fundamentals_pass):
    latest = df.iloc[-1]
    rsi_condition = 40 < latest["RSI"] < 60
    macd_condition = latest["MACD"] > latest["Signal"]
    if fundamentals_pass and rsi_condition and macd_condition:
        return "BUY"
    elif not fundamentals_pass and (latest["RSI"] > 70 or latest["MACD"] < latest["Signal"]):
        return "SELL"
    else:
        return "HOLD"

# --------------------- UI ---------------------
st.title("📊 Nifty Scanner")

# Filters
index_filter = st.selectbox("Select Index", ["All", "Nifty 50", "Nifty Midcap 50", "Nifty Smallcap 50"])
industry_filter = st.text_input("Filter by Industry (optional)").strip().lower()

# Add/Remove Tickers
user_tickers = st.text_area("Add your own tickers (comma separated)", value=",".join(default_tickers))
tickers = [t.strip().upper() for t in user_tickers.split(",") if t.strip()]

if index_filter == "Nifty 50":
    tickers = [t for t in tickers if t in nifty50]
elif index_filter == "Nifty Midcap 50":
    tickers = [t for t in tickers if t in niftymidcap50]
elif index_filter == "Nifty Smallcap 50":
    tickers = [t for t in tickers if t in niftysmallcap50]

# --------------------- PROCESS DATA ---------------------
results = []
for ticker in tickers:
    df = fetch_data(ticker)
    if df is None:
        st.warning(f"⚠ Error fetching data for {ticker} from yfinance.")
        continue
    fund_pass = fundamentals_ok(ticker)
    signal = buy_sell_indicator(df, fund_pass)
    overall_rating = "Strong" if signal == "BUY" else "Weak" if signal == "SELL" else "Neutral"
    industry = "Unknown"  # Can fetch if you have mapping
    if industry_filter and industry_filter not in industry.lower():
        continue
    results.append({
        "Ticker": ticker,
        "Industry": industry,
        "Signal": signal,
        "Overall Rating": overall_rating,
        "TradingView": f"[View Chart](https://www.tradingview.com/chart/?symbol={ticker})"
    })

# --------------------- DISPLAY ---------------------
if results:
    df_display = pd.DataFrame(results)
    st.write(df_display.to_markdown(index=False), unsafe_allow_html=True)

    # CSV Download
    csv = df_display.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Download CSV", data=csv, file_name="nifty_scan.csv", mime="text/csv")
else:
    st.info("No data to display. Adjust filters or tickers.")
