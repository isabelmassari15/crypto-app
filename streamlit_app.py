import streamlit as st
import pandas as pd
import requests
import ta
import plotly.graph_objects as go
from sklearn.ensemble import RandomForestClassifier
import numpy as np

st.set_page_config(layout="wide")

st.title("🧠 AI TRADING PRO MAX (ML + Simulator)")

# ======================
# ASSET + TIMEFRAME
# ======================
asset = st.selectbox("Asset", ["BTCUSDT", "ETHUSDT"])
timeframe = st.selectbox("Timeframe", ["1m", "5m", "30m", "1h"])

# ======================
# BINANCE DATA
# ======================
url = f"https://api.binance.com/api/v3/klines?symbol={asset}&interval={timeframe}&limit=500"
data = requests.get(url).json()

df = pd.DataFrame(data, columns=[
    "time","open","high","low","close","volume",
    "c1","c2","c3","c4","c5","c6"
])

df["time"] = pd.to_datetime(df["time"], unit="ms")

for col in ["open","high","low","close","volume"]:
    df[col] = df[col].astype(float)

# ======================
# INDICATORI
# ======================
df["ma10"] = df["close"].rolling(10).mean()
df["ma20"] = df["close"].rolling(20).mean()
df["rsi"] = ta.momentum.RSIIndicator(df["close"]).rsi()

macd = ta.trend.MACD(df["close"])
df["macd"] = macd.macd()
df["macd_signal"] = macd.macd_signal()

df = df.dropna()

# ======================
# LABEL (TARGET FUTURO)
# ======================
df["future"] = df["close"].shift(-1)
df["target"] = (df["future"] > df["close"]).astype(int)

# ======================
# FEATURES
# ======================
features = ["ma10", "ma20", "rsi", "macd", "macd_signal"]

X = df[features]
y = df["target"]

# ======================
# MODELLO ML
# ======================
model = RandomForestClassifier(n_estimators=100)
model.fit(X, y)

df["ml_prob_up"] = model.predict_proba(X)[:,1] * 100
df["ml_signal"] = model.predict(X)

# ======================
# SIMULATORE CAPITALE
# ======================
capital = 1000
position = 0
equity = []

for i in range(len(df)):
    price = df["close"].iloc[i]
    signal = df["ml_signal"].iloc[i]

    if signal == 1 and position == 0:
        position = capital / price
        capital = 0

    elif signal == 0 and position > 0:
        capital = position * price
        position = 0

    total = capital if position == 0 else position * price
    equity.append(total)

df["equity"] = equity

# ======================
# OUTPUT
# ======================
st.metric("📈 Probabilità salita", f"{df['ml_prob_up'].iloc[-1]:.1f}%")
st.metric("💰 Capitale simulato", f"{df['equity'].iloc[-1]:.2f} $")

# ======================
# GRAFICO CANDLE
# ======================
fig = go.Figure()

fig.add_trace(go.Candlestick(
    x=df["time"],
    open=df["open"],
    high=df["high"],
    low=df["low"],
    close=df["close"]
))

# BUY / SELL ML
buy = df[df["ml_signal"] == 1]
sell = df[df["ml_signal"] == 0]

fig.add_trace(go.Scatter(
    x=buy["time"],
    y=buy["low"] * 0.999,
    mode="markers",
    marker=dict(symbol="triangle-up", size=10, color="green"),
    name="BUY"
))

fig.add_trace(go.Scatter(
    x=sell["time"],
    y=sell["high"] * 1.001,
    mode="markers",
    marker=dict(symbol="triangle-down", size=10, color="red"),
    name="SELL"
))

fig.update_layout(xaxis_rangeslider_visible=False)

st.plotly_chart(fig, use_container_width=True)

# ======================
# EQUITY CURVE
# ======================
st.subheader("💰 Simulatore Capitale")

st.line_chart(df["equity"])

# ======================
# LEGENDA
# ======================
st.subheader("🧠 AI INFO")

st.markdown("""
🧠 ML MODEL:
- Random Forest impara dai dati storici
- predice probabilità prossima candela

💰 SIMULATORE:
- compra quando AI dice BUY
- vende quando AI dice SELL
- calcola crescita capitale

⚠️ NON è consulenza finanziaria
""")
