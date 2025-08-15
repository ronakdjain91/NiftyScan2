import streamlit as st
import pandas as pd
import yfinance as yf
import datetime
import numpy as np

# ---------------------- CONFIG ----------------------
st.set_page_config(page_title="Nifty Scanner", layout="wide")

# Predefined tickers (symbol.NS for NSE)
nifty_50 = ["RELIANCE.NS","TCS.NS","HDFCBANK.NS","ICICIBANK.NS","INFY.NS","HINDUNILVR.NS","ITC.NS","SBIN.NS","BHARTIARTL.NS","BAJFINANCE.NS",
"LICI.NS","HCLTECH.NS","KOTAKBANK.NS","LT.NS","ASIANPAINT.NS","AXISBANK.NS","MARUTI.NS","SUNPHARMA.NS","ULTRACEMCO.NS","NTPC.NS",
"POWERGRID.NS","TITAN.NS","WIPRO.NS","ONGC.NS","M&M.NS","BAJAJFINSV.NS","ADANIENT.NS","ADANIPORTS.NS","COALINDIA.NS","TECHM.NS",
"JSWSTEEL.NS","NESTLEIND.NS","HDFCLIFE.NS","BRITANNIA.NS","TATAMOTORS.NS","TATASTEEL.NS","GRASIM.NS","HEROMOTOCO.NS","BPCL.NS","CIPLA.NS",
"DIVISLAB.NS","HINDALCO.NS","DRREDDY.NS","EICHERMOT.NS","SHREECEM.NS","UPL.NS","BAJAJ-AUTO.NS","SBILIFE.NS","APOLLOHOSP.NS","INDUSINDBK.NS"]

nifty_midcap_50 = ["ABB.NS","ALKEM.NS","APLAPOLLO.NS","AUROPHARMA.NS","BANDHANBNK.NS","BANKBARODA.NS","BERGEPAINT.NS","BHEL.NS","CANBK.NS",
"CHOLAFIN.NS","CROMPTON.NS","DABUR.NS","DALBHARAT.NS","ESCORTS.NS","FEDERALBNK.NS","GODREJCP.NS","HAVELLS.NS","ICICIPRULI.NS","IDFCFIRSTB.NS",
"INDIANB.NS","INDIGO.NS","JINDALSTEL.NS","L&TFH.NS","LICHSGFIN.NS","MANKIND.NS","MUTHOOTFIN.NS","NAUKRI.NS","OBEROIRLTY.NS","PFIZER.NS",
"PIIND.NS","POLYCAB.NS","PRESTIGE.NS","SAIL.NS","SUNTV.NS","TATACHEM.NS","TATACOMM.NS","TATAPOWER.NS","TVSMOTOR.NS","UNIONBANK.NS","VOLTAS.NS",
"ZEEL.NS","GMRINFRA.NS","IRCTC.NS","CONCOR.NS","PAGEIND.NS","TORNTPHARM.NS","LODHA.NS","PETRONET.NS","HINDPETRO.NS"]

nifty_smallcap_50 = ["AARTIIND.NS","ADANIGREEN.NS","ADANIPOWER.NS","AMARAJABAT.NS","ANGELONE.NS","ASTERDM.NS","BEML.NS","CENTURYTEX.NS",
"DEEPAKNTR.NS","FACT.NS","FIVESTAR.NS","GODREJIND.NS","GSPL.NS","GUJGASLTD.NS","HFCL.NS","IDBI.NS","INDIACEM.NS","JBCHEPHARM.NS","JYOTHYLAB.NS",
"KALPATPOWR.NS","KPITTECH.NS","LATENTVIEW.NS","LXCHEM.NS","MAHABANK.NS","MAPMYINDIA.NS","MRPL.NS","NBCC.NS","NIACL.NS","PNBHOUSING.NS",
"POLYMED.NS","RITES.NS","RVNL.NS","SJVN.NS","STAR.NS","STLTECH.NS","SUMICHEM.NS","SUNTECK.NS","SUZLON.NS","SYRMA.NS","TANLA.NS","TEJASNET.NS",
"TRIDENT.NS","UCOBANK.NS","VGUARD.NS","VMART.NS","WHIRLPOOL.NS","YESBANK.NS","ZENSARTECH.NS"]

# Merge all for default
all_tickers = list(set(nifty_50 + nifty_midcap_50 + nifty_smallcap_50))

# ---------------------- FUNCTIONS ----------------------
def get_fundamentals(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        pe_ratio = info.get("trailingPE", None)
        pb_ratio = info.get("priceToBook", None)
        debt_equity = info.get("debtToEquity", None)
        sector = info.get("sector", "Unknown")
        
        fundamentals_ok = False
        score = 0
        if pe_ratio and pe_ratio < 25:
            score += 1
        if pb_ratio and pb_ratio < 5:
            score += 1
        if debt_equity and debt_equity < 100:
            score += 1
        
        if score >= 2:
            fundamentals_ok = True
        
        return pe_ratio, pb_ratio, debt_equity, sector, fundamentals_ok
    except:
        return None, None, None, "Unknown", False

def get_technicals(df):
    df['EMA12'] = df['Close'].ewm(span=12).mean()
    df['EMA26'] = df['Close'].ewm(span=26).mean()
    df['MACD'] = df['EMA12'] - df['EMA26']
    df['Signal'] = df['MACD'].ewm(span=9).mean()
    macd_signal = df['MACD'].iloc[-1] > df['Signal'].iloc[-1]
    
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    latest_rsi = rsi.iloc[-1]
    rsi_signal = 40 < latest_rsi < 60
    
    return latest_rsi, macd_signal, rsi_signal

def buy_sell_indicator(f_ok, macd_signal, rsi_signal):
    if f_ok and macd_signal and rsi_signal:
        return "BUY", 3
    elif f_ok and (macd_signal or rsi_signal):
        return "HOLD", 2
    else:
        return "SELL", 1

# ---------------------- UI ----------------------
st.title("📊 Nifty Stock Scanner (Fundamental + Technical)")
index_filter = st.selectbox("Select Index", ["All", "Nifty 50", "Midcap 50", "Smallcap 50"])
industry_filter = st.text_input("Filter by Industry (leave blank for all)")

if index_filter == "Nifty 50":
    tickers = nifty_50
elif index_filter == "Midcap 50":
    tickers = nifty_midcap_50
elif index_filter == "Smallcap 50":
    tickers = nifty_smallcap_50
else:
    tickers = all_tickers

# Add/remove tickers
custom_tickers = st.text_area("Add/Remove Tickers (comma separated, .NS format)", value=",".join(tickers))
tickers = [t.strip() for t in custom_tickers.split(",") if t.strip()]

# ---------------------- DATA ----------------------
data_list = []
start_date = datetime.date.today() - datetime.timedelta(days=365)
end_date = datetime.date.today()

for ticker in tickers:
    try:
        df = yf.download(ticker, start=start_date, end=end_date)
        if df.empty:
            continue
        pe, pb, de, sector, f_ok = get_fundamentals(ticker)
        rsi, macd_signal, rsi_signal = get_technicals(df)
        signal, rating = buy_sell_indicator(f_ok, macd_signal, rsi_signal)
        if industry_filter and industry_filter.lower() not in sector.lower():
            continue
        data_list.append({
            "Ticker": ticker,
            "Sector": sector,
            "P/E": pe,
            "P/B": pb,
            "Debt/Equity": de,
            "RSI": round(rsi, 2),
            "Signal": signal,
            "Overall Rating": rating,
            "TradingView": f"https://in.tradingview.com/symbols/NSE-{ticker.replace('.NS','')}/"
        })
    except:
        pass

df_display = pd.DataFrame(data_list)

# ---------------------- DISPLAY ----------------------
if not df_display.empty:
    st.dataframe(df_display, use_container_width=True)
    
    # CSV download
    csv = df_display.to_csv(index=False)
    st.download_button("Download CSV", csv, "nifty_scan.csv", "text/csv")
else:
    st.warning("No data found.")
