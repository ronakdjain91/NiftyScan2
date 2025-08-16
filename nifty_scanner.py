import streamlit as st
import pandas as pd
import yfinance as yf
import ta
import plotly.graph_objects as go
from datetime import date, timedelta

# --- Page Configuration ---
st.set_page_config(
    page_title="Pro Stock Screener",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Functions for Data Retrieval and Analysis ---
@st.cache_data
def get_stock_data(ticker, start_date, end_date):
    """Fetches historical stock data for a given ticker."""
    try:
        data = yf.download(ticker, start=start_date, end=end_date)
        return data
    except Exception as e:
        st.error(f"Error fetching data for {ticker}: {e}")
        return None

def apply_technical_indicators(df):
    """Applies a suite of technical indicators to the dataframe."""
    df['SMA_50'] = ta.trend.sma_indicator(df['Close'], window=50)
    df['SMA_200'] = ta.trend.sma_indicator(df['Close'], window=200)
    df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
    df['MACD'] = ta.trend.macd(df['Close'])
    df['MACD_Signal'] = ta.trend.macd_signal(df['Close'])
    return df

def analyze_stock(df, ticker):
    """Generates a buy/sell signal based on technical analysis."""
    if df is None or len(df) < 200:
        return {"ticker": ticker, "signal": "N/A", "reason": "Insufficient data"}
    
    last_row = df.iloc[-1]
    
    # Check for Buy Signal: Bullish 50/200 MA Crossover + RSI in a healthy range
    buy_condition = (
        last_row['SMA_50'] > last_row['SMA_200'] and
        df.iloc[-2]['SMA_50'] <= df.iloc[-2]['SMA_200'] and
        30 < last_row['RSI'] < 70
    )
    
    # Check for Sell Signal: Bearish 50/200 MA Crossover
    sell_condition = (
        last_row['SMA_50'] < last_row['SMA_200'] and
        df.iloc[-2]['SMA_50'] >= df.iloc[-2]['SMA_200']
    )
    
    if buy_condition:
        return {"ticker": ticker, "signal": "BUY", "reason": "Bullish MA Crossover and healthy RSI."}
    elif sell_condition:
        return {"ticker": ticker, "signal": "SELL", "reason": "Bearish MA Crossover."}
    else:
        return {"ticker": ticker, "signal": "HOLD", "reason": "No clear signal."}

def create_candlestick_chart(df, ticker):
    """Creates a visually stunning candlestick chart with moving averages."""
    fig = go.Figure(data=[go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name="Candlestick"
    )])
    
    # Add Moving Averages
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], mode='lines', name='SMA 50', line=dict(color='orange', width=2)))
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_200'], mode='lines', name='SMA 200', line=dict(color='purple', width=2)))

    # Customize Layout
    fig.update_layout(
        title=f"<b>{ticker}</b> Candlestick Chart",
        title_x=0.5,
        xaxis_title="Date",
        yaxis_title="Price (USD)",
        xaxis_rangeslider_visible=False,
        template="plotly_dark",
        height=600
    )
    return fig

# --- App Layout and UI ---
st.title("Pro Stock Screener 📈")

with st.sidebar:
    st.header("Screener Filters")
    ticker_input = st.text_input("Enter Ticker Symbols (e.g., AAPL, MSFT, GOOG)", "AAPL, MSFT, GOOG")
    tickers = [t.strip().upper() for t in ticker_input.split(',')]
    
    # Date range selector
    today = date.today()
    start_date = st.date_input("Start Date", today - timedelta(days=365))
    end_date = st.date_input("End Date", today)

# --- Main Content ---
tab1, tab2 = st.tabs(["Recommendations", "Detailed Analysis"])

with tab1:
    st.header("Daily Recommendations")
    
    recommendations = []
    with st.spinner("Analyzing stocks..."):
        for ticker in tickers:
            data = get_stock_data(ticker, start_date, end_date)
            if data is not None and not data.empty:
                data = apply_technical_indicators(data)
                analysis = analyze_stock(data, ticker)
                if analysis['signal'] != 'HOLD' and analysis['signal'] != 'N/A':
                    recommendations.append(analysis)
    
    if recommendations:
        rec_df = pd.DataFrame(recommendations)
        st.dataframe(rec_df, use_container_width=True)
    else:
        st.info("No BUY or SELL signals found based on current criteria.")

with tab2:
    st.header("Detailed Stock Analysis")
    selected_ticker = st.selectbox("Select a Ticker for detailed view", tickers)

    if selected_ticker:
        st.markdown(f"### Analysis for **{selected_ticker}**")
        data = get_stock_data(selected_ticker, start_date, end_date)
        
        if data is not None and not data.empty:
            data = apply_technical_indicators(data)
            
            # Display Candlestick Chart
            fig = create_candlestick_chart(data, selected_ticker)
            st.plotly_chart(fig, use_container_width=True)
            
            # Display Key Metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Current Price", f"${data['Close'].iloc[-1]:.2f}")
            with col2:
                st.metric("RSI", f"{data['RSI'].iloc[-1]:.2f}", delta=f"{data['RSI'].iloc[-1] - data['RSI'].iloc[-2]:.2f}")
            with col3:
                st.metric("MACD", f"{data['MACD'].iloc[-1]:.2f}")
            
            # Display recent data in a table
            st.markdown("### Recent Technical Data")
            st.dataframe(data[['Close', 'Volume', 'SMA_50', 'SMA_200', 'RSI', 'MACD']].tail(10).round(2), use_container_width=True)

# --- How to Run the App ---
st.markdown("---")
st.markdown("""
### How to run this app:
1.  Save the code above as `app.py`.
2.  Save the requirements list as `requirements.txt`.
3.  Open your terminal or command prompt in the same directory.
4.  Run `pip install -r requirements.txt` to install the libraries.
5.  Run `streamlit run app.py` to launch the web app.
""")
The video below provides a visual walkthrough of building a stock dashboard using Python and Streamlit, which can serve as a great reference for this project.

[Python - Stock Dashboards with YFinance and Streamlit](https://www.youtube.com/watch?v=GSDdb0CDsR8)
http://googleusercontent.com/youtube_content/1 *YouTube video views will be stored in your YouTube History, and your data will be stored and used by YouTube according to its [Terms of Service](https://www.youtube.com/static?template=terms)*


