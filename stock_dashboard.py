import yfinance as yf
import dash
from dash import dcc, html
import plotly.graph_objs as go

ticker = "1155.KL"  # Maybank
stock = yf.Ticker(ticker)
hist = stock.history(period="6mo")

# Calculate moving averages
hist["MA20"] = hist["Close"].rolling(20).mean()
hist["MA50"] = hist["Close"].rolling(50).mean()

# Generate signal
signal = "Buy" if hist["MA20"].iloc[-1] > hist["MA50"].iloc[-1] else "Sell"

app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1(f"{ticker} Stock Dashboard"),

    # Price chart with moving averages
    dcc.Graph(
        id="price-chart",
        figure={
            "data": [
                go.Candlestick(
                    x=hist.index,
                    open=hist["Open"],
                    high=hist["High"],
                    low=hist["Low"],
                    close=hist["Close"],
                    name="Price"
                ),
                go.Line(x=hist.index, y=hist["MA20"], name="MA20"),
                go.Line(x=hist.index, y=hist["MA50"], name="MA50")
            ],
            "layout": go.Layout(title="Price & Moving Averages")
        }
    ),

    # Volume chart
    dcc.Graph(
        id="volume-chart",
        figure={
            "data": [go.Bar(x=hist.index, y=hist["Volume"], name="Volume")],
            "layout": go.Layout(title="Trading Volume")
        }
    ),

    # Key metrics + signal
    html.Div([
        html.P(f"Current Price: {stock.info.get('currentPrice', 'N/A')}"),
        html.P(f"Market Cap: {stock.info.get('marketCap', 'N/A')}"),
        html.P(f"P/E Ratio: {stock.info.get('forwardPE', 'N/A')}"),
        html.H2(f"Signal: {signal}", style={"color": "green" if signal == "Buy" else "red"})
    ])
])

if __name__ == "__main__":
    app.run(debug=True)
