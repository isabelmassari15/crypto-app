import streamlit as st
import pandas as pd
import requests
import ta
import plotly.graph_objects as go
import numpy as np
from sklearn.ensemble import RandomForestClassifier

st.set_page_config(layout="wide")

st.title("🧠 AI TRADING BOT PRO (STABILE + ML)")

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

# pulizia base
df = df.replace([np.inf, -np.inf], np.nan)

# ======================
# LABEL (FUTURO)
# ======================
df["future"] = df["close"].shift(-1)
df["target"] = (df["future"] > df["close"]).astype(int)

# ======================
# DATASET ML PULITO
# ======================
features = ["ma10", "ma20", "rsi", "macd", "macd_signal"]

df_ml = df[features + ["target"]].dropna()

X = df_ml[features]
y = df_ml["target"]

# ======================
# MODELLO ML
# ======================
model = RandomForestClassifier(
    n_estimators=100,
    random_state=42
)

model.fit(X, y)

df.loc[df_ml.index, "ml_prob_up"] = model.predict_proba(X)[:, 1] * 100
df.loc[df_ml.index, "ml_signal"] = model.predict(X)

df = df.dropna()

# ======================
# PROBABILITÀ ULTIMA
# ======================
up = df["ml_prob_up"].iloc[-1]
last_signal = df["ml_signal"].iloc[-1]

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
# DASHBOARD
# ======================
col1, col2 = st.columns(2)

with col1:
    st.metric("📈 Probabilità salita", f"{up:.1f}%")

with col2:
    st.metric("💰 Capitale simulato", f"{df['equity'].iloc[-1]:.2f} $")

st.metric("🎯 Segnale", "BUY" if last_signal == 1 else "SELL")

# ======================
# GRAFICO CANDLE
# ======================
fig = go.Figure()

fig.add_trace(go.Candlestick(
    x=df["time"],
    open=df["open"],
    high=df["high"],
    low=df["low"],
    close=df["close"],
    name="Candles"
))

# BUY / SELL
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
# EQUITY
# ======================
st.subheader("💰 Simulatore Capitale")
st.line_chart(df["equity"])

# ======================
# LEGENDA
# ======================
st.subheader("🧠 Legenda AI")

st.markdown("""
🧠 MODELLO ML:
- Random Forest su indicatori tecnici
- predice direzione prossima candela

💰 SIMULATORE:
- compra quando BUY
- vende quando SELL
- simula crescita capitale

⚠️ NON è consulenza finanziaria
""")
