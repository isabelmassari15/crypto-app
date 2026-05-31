import streamlit as st
import pandas as pd
import requests
import ta
import plotly.graph_objects as go

st.title("🚀 Crypto Bot BTC + ETH")

symbol = st.selectbox("Scegli crypto", ["BTCUSDT", "ETHUSDT"])

# CoinGecko (NON SI BLOCCA)
if symbol == "BTCUSDT":
    coin_id = "bitcoin"
else:
    coin_id = "ethereum"

url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days=7"

data = requests.get(url).json()

prices = data["prices"]

df = pd.DataFrame(prices, columns=["time", "price"])
df["price"] = df["price"].astype(float)
df["close"] = df["price"]

df["ma20"] = df["close"].rolling(20).mean()
df["ma50"] = df["close"].rolling(50).mean()
df["rsi"] = ta.momentum.RSIIndicator(df["close"]).rsi()

df["signal"] = 0
df.loc[(df["ma20"] > df["ma50"]) & (df["rsi"] < 70), "signal"] = 1
df.loc[(df["ma20"] < df["ma50"]) & (df["rsi"] > 30), "signal"] = -1

fig = go.Figure()
fig.add_trace(go.Scatter(y=df["close"], name="Prezzo"))
fig.add_trace(go.Scatter(y=df["ma20"], name="MA20"))
fig.add_trace(go.Scatter(y=df["ma50"], name="MA50"))

buy = df[df["signal"] == 1]
fig.add_trace(go.Scatter(x=buy.index, y=buy["close"], mode="markers", name="BUY"))

sell = df[df["signal"] == -1]
fig.add_trace(go.Scatter(x=sell.index, y=sell["close"], mode="markers", name="SELL"))

st.plotly_chart(fig)

st.subheader("RSI")
st.line_chart(df["rsi"])

last = df["signal"].iloc[-1]

if last == 1:
    st.success("📈 BUY")
elif last == -1:
    st.error("📉 SELL")
else:
    st.warning("⏸️ HOLD")
