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
    macd_lin_
