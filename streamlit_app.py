import streamlit as st
import pandas as pd
from binance.client import Client
import ta
import plotly.graph_objects as go

st.title("🚀 Crypto Bot BTC + ETH (Binance)")

# Binance (public, no API key needed)
client = Client()

# Selezione asset
symbol = st.selectbox("Scegli crypto", ["BTCUSDT", "ETHUSDT"])

# Dati da Binance
klines = client.get_klines(symbol=symbol, interval=Client.KLINE_INTERVAL_1HOUR, limit=200)

df = pd.DataFrame(klines, columns=[
    "time","open","high","low","close","volume",
    "close_time","qav","trades","tbbav","tbqav","ignore"
])

df["close"] = df["close"].astype(float)

# Indicatori
df["ma20"] = df["close"].rolling(20).mean()
df["ma50"] = df["close"].rolling(50).mean()
df["rsi"] = ta.momentum.RSIIndicator(df["close"]).rsi()

# Segnali
df["signal"] = 0
df.loc[(df["ma20"] > df["ma50"]) & (df["rsi"] < 70), "signal"] = 1  # BUY
df.loc[(df["ma20"] < df["ma50"]) & (df["rsi"] > 30), "signal"] = -1 # SELL

# Grafico
fig = go.Figure()

fig.add_trace(go.Scatter(y=df["close"], name="Prezzo"))
fig.add_trace(go.Scatter(y=df["ma20"], name="MA20"))
fig.add_trace(go.Scatter(y=df["ma50"], name="MA50"))

# BUY
buy_signals = df[df["signal"] == 1]
fig.add_trace(go.Scatter(
    x=buy_signals.index,
    y=buy_signals["close"],
    mode="markers",
    name="BUY",
    marker=dict(symbol="triangle-up", size=10)
))

# SELL
sell_signals = df[df["signal"] == -1]
fig.add_trace(go.Scatter(
    x=sell_signals.index,
    y=sell_signals["close"],
    mode="markers",
    name="SELL",
    marker=dict(symbol="triangle-down", size=10)
))

st.plotly_chart(fig)

# RSI
st.subheader("RSI")
st.line_chart(df["rsi"])

# Ultimo segnale
last_signal = df["signal"].iloc[-1]

if last_signal == 1:
    st.success("📈 SEGNALE: BUY")
elif last_signal == -1:
    st.error("📉 SEGNALE: SELL")
else:
    st.warning("⏸️ NESSUN SEGNALE")
