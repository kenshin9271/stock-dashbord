import os
import yfinance as yf
import dash
from dash import dcc, html
import plotly.graph_objs as go
import numpy as np
import pandas as pd

# --- Stock setup ---
ticker = "1155.KL"  # Maybank
stock = yf.Ticker(ticker)
hist = stock.history(period="6mo")

# --- Moving averages ---
hist["MA20"] = hist["Close"].rolling(20).mean()
hist["MA50"] = hist["Close"].rolling(50).mean()

# --- RSI calculation (14-day) ---
delta = hist["Close"].diff()
gain = delta.where(delta > 0, 0)
loss = -delta.where(delta < 0, 0)
avg_gain = gain.rolling(14).mean()
avg_loss = loss.rolling(14).mean()
rs = avg_gain / avg_loss
hist["RSI"] = 100 - (100 / (1 + rs))
hist["RSI"] = hist["RSI"].fillna(0)

# --- MACD (12,26,9) ---
hist["EMA12"] = hist["Close"].ewm(span=12, adjust=False).mean()
hist["EMA26"] = hist["Close"].ewm(span=26, adjust=False).mean()
hist["MACD"] = hist["EMA12"] - hist["EMA26"]
hist["Signal"] = hist["MACD"].ewm(span=9, adjust=False).mean()

# --- Bollinger Bands (20-day) ---
hist["BB_Mid"] = hist["Close"].rolling(20).mean()
hist["BB_Upper"] = hist["BB_Mid"] + 2 * hist["Close"].rolling(20).std()
hist["BB_Lower"] = hist["BB_Mid"] - 2 * hist["Close"].rolling(20).std()

# --- ATR (14-day) ---
high_low = hist["High"] - hist["Low"]
high_close = np.abs(hist["High"] - hist["Close"].shift())
low_close = np.abs(hist["Low"] - hist["Close"].shift())
tr = high_low.combine(high_close, max).combine(low_close, max)
hist["ATR"] = tr.rolling(14).mean()

# --- VWAP ---
hist["CumVol"] = hist["Volume"].cumsum()
hist["CumPV"] = (hist["Close"] * hist["Volume"]).cumsum()
hist["VWAP"] = hist["CumPV"] / hist["CumVol"]

# --- Stochastic Oscillator (14-day) ---
low14 = hist["Low"].rolling(14).min()
high14 = hist["High"].rolling(14).max()
hist["%K"] = (hist["Close"] - low14) * 100 / (high14 - low14)
hist["%D"] = hist["%K"].rolling(3).mean()

# --- Generate signals ---
ma_signal = "Buy" if hist["MA20"].iloc[-1] > hist["MA50"].iloc[-1] else "Sell"
rsi_value = hist["RSI"].iloc[-1]
rsi_signal = "Buy" if rsi_value < 30 else "Sell" if rsi_value > 70 else "Hold"
macd_signal = "Buy" if hist["MACD"].iloc[-1] > hist["Signal"].iloc[-1] else "Sell"
boll_signal = "Buy" if hist["Close"].iloc[-1] < hist["BB_Lower"].iloc[-1] else "Sell" if hist["Close"].iloc[-1] > hist["BB_Upper"].iloc[-1] else "Hold"
stoch_signal = "Buy" if hist["%K"].iloc[-1] < 20 else "Sell" if hist["%K"].iloc[-1] > 80 else "Hold"

# --- Dash app setup ---
app = dash.Dash(__name__)
server = app.server

app.layout = html.Div([
    html.H1(f"{ticker} Stock Dashboard"),

    # Price chart with MA + Bollinger Bands
    dcc.Graph(
        id="price-chart",
        figure={
            "data": [
                go.Candlestick(x=hist.index, open=hist["Open"], high=hist["High"],
                               low=hist["Low"], close=hist["Close"], name="Price"),
                go.Scatter(x=hist.index, y=hist["MA20"], name="MA20", mode="lines"),
                go.Scatter(x=hist.index, y=hist["MA50"], name="MA50", mode="lines"),
                go.Scatter(x=hist.index, y=hist["BB_Upper"], name="BB Upper", mode="lines", line=dict(color="red")),
                go.Scatter(x=hist.index, y=hist["BB_Lower"], name="BB Lower", mode="lines", line=dict(color="green"))
            ],
            "layout": go.Layout(title="Price, MA & Bollinger Bands")
        }
    ),

    # RSI chart
    dcc.Graph(
        id="rsi-chart",
        figure={
            "data": [go.Scatter(x=hist.index, y=hist["RSI"], name="RSI", mode="lines", line=dict(color="purple"))],
            "layout": go.Layout(title="Relative Strength Index (RSI)", yaxis=dict(range=[0, 100]))
        }
    ),

    # MACD chart
    dcc.Graph(
        id="macd-chart",
        figure={
            "data": [
                go.Scatter(x=hist.index, y=hist["MACD"], name="MACD", mode="lines"),
                go.Scatter(x=hist.index, y=hist["Signal"], name="Signal", mode="lines")
            ],
            "layout": go.Layout(title="MACD")
        }
    ),

    # ATR chart
    dcc.Graph(
        id="atr-chart",
        figure={
            "data": [go.Scatter(x=hist.index, y=hist["ATR"], name="ATR", mode="lines")],
            "layout": go.Layout(title="Average True Range (ATR)")
        }
    ),

    # VWAP chart
    dcc.Graph(
        id="vwap-chart",
        figure={
            "data": [go.Scatter(x=hist.index, y=hist["VWAP"], name="VWAP", mode="lines")],
            "layout": go.Layout(title="VWAP")
        }
    ),

    # Stochastic Oscillator chart
    dcc.Graph(
        id="stoch-chart",
        figure={
            "data": [
                go.Scatter(x=hist.index, y=hist["%K"], name="%K", mode="lines"),
                go.Scatter(x=hist.index, y=hist["%D"], name="%D", mode="lines")
            ],
            "layout": go.Layout(title="Stochastic Oscillator", yaxis=dict(range=[0, 100]))
        }
    ),

    # Key metrics + signals
    html.Div([
        html.P(f"Current Price: {stock.info.get('currentPrice', 'N/A')}"),
        html.P(f"Market Cap: {stock.info.get('marketCap', 'N/A')}"),
        html.P(f"P/E Ratio: {stock.info.get('forwardPE', 'N/A')}"),
        html.H2(f"MA Signal: {ma_signal}"),
        html.H2(f"RSI Signal: {rsi_signal} (RSI={rsi_value:.2f})"),
        html.H2(f"MACD Signal: {macd_signal}"),
        html.H2(f"Bollinger Signal: {boll_signal}"),
        html.H2(f"Stochastic Signal: {stoch_signal}")
    ])
])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8050")), debug=False)
