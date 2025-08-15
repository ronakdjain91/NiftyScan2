import streamlit as st
import pandas as pd
import yfinance as yf
import datetime
import numpy as np

# ------------------- Ticker Lists -------------------
nifty_50 = ["ADANIPORTS.NS","ASIANPAINT.NS","AXISBANK.NS","BAJAJ-AUTO.NS","BAJFINANCE.NS",
"BAJAJFINSV.NS","BHARTIARTL.NS","BPCL.NS","BRITANNIA.NS","CIPLA.NS","COALINDIA.NS",
"DIVISLAB.NS","DRREDDY.NS","EICHERMOT.NS","GRASIM.NS","HCLTECH.NS","HDFCBANK.NS",
"HDFCLIFE.NS","HEROMOTOCO.NS","HINDALCO.NS","HINDUNILVR.NS","ICICIBANK.NS",
"INDUSINDBK.NS","INFY.NS","ITC.NS","JSWSTEEL.NS","KOTAKBANK.NS","LT.NS","M&M.NS",
"MARUTI.NS","NESTLEIND.NS","NTPC.NS","ONGC.NS","POWERGRID.NS","RELIANCE.NS",
"SBILIFE.NS","SBIN.NS","SUNPHARMA.NS","TATACONSUM.NS","TATAMOTORS.NS","TATASTEEL.NS",
"TCS.NS","TECHM.NS","TITAN.NS","ULTRACEMCO.NS","UPL.NS","WIPRO.NS"]

nifty_midcap_50 = ["ABBOTINDIA.NS","ALKEM.NS","AUROPHARMA.NS","BALKRISIND.NS","BANKINDIA.NS",
"BHEL.NS","CANBK.NS","CHAMBLFERT.NS","CROMPTON.NS","ESCORTS.NS","FEDERALBNK.NS",
"GUJGASLTD.NS","INDHOTEL.NS","JINDALSTEL.NS","L&TFH.NS","LICHSGFIN.NS","MFSL.NS",
"MGL.NS","MOTHERSON.NS","MPHASIS.NS","OIL.NS","PETRONET.NS","PIIND.NS","PFC.NS",
"PGHH.NS","PNB.NS","POLYCAB.NS","SAIL.NS","SUNTV.NS","TATACHEM.NS","TATAPOWER.NS",
"TVSMOTOR.NS","UNIONBANK.NS","VOLTAS.NS","ZYDUSLIFE.NS"]

nifty_smallcap_50 = ["ADANIGREEN.NS","ASTERDM.NS","BIRLACORPN.NS","CARBORUNIV.NS",
"COFORGE.NS","CUMMINSIND.NS","DATAPATTNS.NS","ELGIEQUIP.NS","FORTIS.NS","GODREJPROP.NS",
"HUDCO.NS","IBULHSGFIN.NS","IPCALAB.NS","JKCEMENT.NS","KPITTECH.NS","LATENTVIEW.NS",
"LUXIND.NS","MAHABANK.NS","NHPC.NS","PERSISTENT.NS","RADICO.NS","RBLBANK.NS","RECLTD.NS",
"SUPREMEIND.NS","TIMKEN.NS","TRIDENT.NS","UJJIVANSFB.NS","VMART.NS","YESBANK.NS"]

# Combine all for default
all_tickers = nifty_50 + nifty_midcap_50 + nifty_smallcap_50

# ------------------- Functions -------------------
def get_fundamentals(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
    try:
        pe_ratio = info.get("trailingPE", None)
        pb_ratio = info.get("priceToBook", None)
        sector = info.get("sector", "Unknown")
        fundamentals_ok = pe_ratio is not None and pb_ratio is not None and pe_ratio < 30 and pb_ratio < 5
        return fundamentals_ok, pe_ratio, pb_ratio, sector
    except:
        return False, None, None, "Unknown"

def calculate_technical_indicators(df):
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    df['EMA12'] = df['Close'].ewm(span=12).mean()
    df['EMA26'] = df['Close'].ewm(span=26).mean()
    df['MACD'] = df['EMA12'] - df['EMA26']
    df['Signal'] = df['MACD'].ewm(span=9).mean()
    return df

def buy_sell_indicator(df, fundamentals_ok):
    latest = df.iloc[-1]
    ma_condition = latest['EMA20'] > latest['EMA50']
    rsi_condition = latest['RSI'] < 60 and latest['RSI'] > 40
    macd_condition = latest['MACD'] > latest['Signal']
    if fundamentals_ok and ma_condition and rsi_condition and macd_condition:
        return "BUY"
    elif not fundamentals_ok or (not ma_condition and not macd_condition):
        return "SELL"
    else:
        return "HOLD"

# ------------------- Streamlit App -------------------
st.set_page_config(page_title="Nifty Scanner", layout="wide")
st.title("📈 Nifty Stock Scanner")

index_filter = st.selectbox("Select Index", ["All", "Nifty 50", "Nifty Midcap 50", "Nifty Smallcap 50"])
industry_filter = st.text_input("Filter by Industry (optional)")

if index_filter == "Nifty 50":
    tickers = nifty_50
elif index_filter == "Nifty Midcap 50":
    tickers = nifty_midcap_50
elif index_filter == "Nifty Smallcap 50":
    tickers = nifty_smallcap_50
else:
    tickers = all_tickers

custom_ticker = st.text_input("Add custom ticker (with .NS):")
if custom_ticker:
    tickers.append(custom_ticker)

if st.button("Run Scan"):
    results = []
    end = datetime.datetime.now()
    start = end - datetime.timedelta(days=365)

    for ticker in tickers:
        try:
            df = yf.download(ticker, start=start, end=end)
            if df.empty:
                continue
            df = calculate_technical_indicators(df)
            fundamentals_ok, pe, pb, sector = get_fundamentals(ticker)
            if industry_filter and industry_filter.lower() not in sector.lower():
                continue
            signal = buy_sell_indicator(df, fundamentals_ok)
            rating = "Strong Buy" if signal == "BUY" else "Avoid" if signal == "SELL" else "Neutral"
            tradingview_link = f"https://www.tradingview.com/symbols/NSE-{ticker.replace('.NS','')}/"
            results.append([ticker, sector, pe, pb, signal, rating, tradingview_link])
        except:
            pass

    df_display = pd.DataFrame(results, columns=["Ticker", "Sector", "P/E", "P/B", "Signal", "Overall Rating", "TradingView"])
    st.dataframe(df_display, use_container_width=True)

    csv = df_display.to_csv(index=False)
    st.download_button("Download CSV", csv, "nifty_scan_results.csv", "text/csv")
