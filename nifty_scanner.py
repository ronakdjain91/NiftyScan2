import streamlit as st
import yfinance as yf
import pandas as pd
import datetime as dt

# =========================
# Utility Functions
# =========================
def get_fundamentals(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        pe_ratio = info.get('trailingPE', None)
        pb_ratio = info.get('priceToBook', None)
        debt_to_equity = info.get('debtToEquity', None)
        roe = info.get('returnOnEquity', None)

        fundamentals_ok = (
            pe_ratio is not None and pe_ratio < 30 and
            pb_ratio is not None and pb_ratio < 5 and
            debt_to_equity is not None and debt_to_equity < 100 and
            roe is not None and roe > 0.1
        )

        return fundamentals_ok, pe_ratio, pb_ratio, debt_to_equity, roe
    except Exception:
        return False, None, None, None, None


def get_technical_indicators(df):
    df['MA200'] = df['Close'].rolling(window=200).mean()

    # RSI calculation
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # MACD calculation
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

    return df


def buy_sell_indicator(df, fundamentals_ok):
    latest_price = float(df['Close'].iloc[-1])
    latest_rsi = float(df['RSI'].iloc[-1])
    latest_ma200 = float(df['MA200'].iloc[-1])
    latest_macd = float(df['MACD'].iloc[-1])
    latest_signal = float(df['Signal'].iloc[-1])

    price_condition = latest_price > latest_ma200
    rsi_condition = 40 < latest_rsi < 60
    macd_condition = latest_macd > latest_signal  # Bullish

    if fundamentals_ok and price_condition and rsi_condition and macd_condition:
        return "BUY"
    elif not fundamentals_ok:
        return "HOLD (Fundamentals weak)"
    else:
        return "SELL"


# =========================
# Streamlit UI
# =========================
st.title("📈 Nifty Stock Scanner with Fundamentals + Technicals")
st.write("Mid-term investment signals with TradingView links")

# Ticker management
default_tickers = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS"]
tickers = st.session_state.get("tickers", default_tickers)

col1, col2 = st.columns(2)
with col1:
    add_ticker = st.text_input("Add NSE Ticker (e.g., ITC.NS)")
    if st.button("Add"):
        if add_ticker and add_ticker not in tickers:
            tickers.append(add_ticker)
            st.session_state["tickers"] = tickers

with col2:
    remove_ticker = st.selectbox("Remove Ticker", options=[""] + tickers)
    if st.button("Remove"):
        if remove_ticker and remove_ticker in tickers:
            tickers.remove(remove_ticker)
            st.session_state["tickers"] = tickers

# Date range for 1 year
end = dt.date.today()
start = end - dt.timedelta(days=365)

# Data display
data_list = []

for ticker in tickers:
    try:
        df = yf.download(ticker, start=start, end=end)
        if df.empty:
            continue

        fundamentals_ok, pe, pb, debt, roe = get_fundamentals(ticker)
        df = get_technical_indicators(df)
        signal = buy_sell_indicator(df, fundamentals_ok)

        tradingview_url = f"https://www.tradingview.com/symbols/NSE-{ticker.replace('.NS', '')}/"

        data_list.append({
            "Ticker": ticker,
            "P/E": pe,
            "P/B": pb,
            "Debt/Equity": debt,
            "ROE": roe,
            "Signal": signal,
            "TradingView": f"[View Chart]({tradingview_url})"
        })

    except Exception as e:
        st.error(f"Error processing {ticker}: {e}")

if data_list:
    df_display = pd.DataFrame(data_list)
    st.markdown(df_display.to_markdown(index=False), unsafe_allow_html=True)
else:
    st.warning("No data available for selected tickers.")
