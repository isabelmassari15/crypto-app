import streamlit as st
import pandas as pd
import requests
import ta
import plotly.graph_objects as go

st.title("🚀 Crypto Bot BTC + ETH")

symbol = st.selectbox("Scegli crypto", ["BTCUSDT", "ETHUSDT"])

url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1h&limit=200"
data = requests.get(url).json()

df = pd.DataFrame(data, columns=[
    "time","open","high","low","close","volume",
    "close_time","qav","trades","tbbav","tbqav","ignore"
])

df["close"] = df["close"].astype(float)

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
