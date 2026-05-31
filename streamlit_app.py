import streamlit as st
import pandas as pd
import requests
import ta
import plotly.graph_objects as go
import numpy as np
from sklearn.ensemble import RandomForestClassifier

st.set_page_config(layout="wide")
st.title("🧠 AI TRADING BOT PRO — STABLE V3 (FIX DATA)")

# ======================
# INPUT
# ======================
asset = st.selectbox("Asset", ["BTCUSDT", "ETHUSDT"])
timeframe = st.selectbox("Timeframe", ["1m", "5m", "15m", "30m", "1h"])

# ======================
# PIÙ DATI (FIX PRINCIPALE)
# ======================
url = f"https://api.binance.com/api/v3/klines?symbol={asset}&interval={timeframe}&limit=1500"
data = requests.get(url).json()

df = pd.DataFrame(data, columns=[
    "time","open","high","low","close","volume",
    "c1","c2","c3","c4","c5","c6"
])

df["time"] = pd.to_datetime(df["time"], unit="ms")

for col in ["open","high","low","close","volume"]:
    df[col] = df[col].astype(float)

# ======================
# INDICATORI (MENO AGGRESSIVI)
# ======================
df["ma10"] = df["close"].rolling(10).mean()
df["ma20"] = df["close"].rolling(20).mean()

df["rsi"] = ta.momentum.RSIIndicator(df["close"], window=14).rsi()

macd = ta.trend.MACD(df["close"], window_slow=26, window_fast=12, window_sign=9)
df["macd"] = macd.macd()
df["macd_signal"] = macd.macd_signal()

df["future"] = df["close"].shift(-1)
df["target"] = (df["future"] > df["close"]).astype(int)

features = ["ma10", "ma20", "rsi", "macd", "macd_signal"]

# ======================
# CLEAN SOLO ML
# ======================
df_ml = df[features + ["target"]].copy()

# FIX IMPORTANTE: NON distruggere tutto il df
df_ml = df_ml.replace([np.inf, -np.inf], np.nan)

# riempimento invece di drop massivo
df_ml = df_ml.ffill().bfill()

df["ml_signal"] = np.nan
df["ml_prob_up"] = np.nan

# ======================
# MODEL
# ======================
X = df_ml[features]
y = df_ml["target"]

# sicurezza vera
if len(df_ml) < 120:

    st.warning("⚠️ Dataset piccolo → modello semplificato (NON fallback totale)")

    df["ml_signal"] = (df["ma10"] > df["ma20"]).astype(int)
    df["ml_prob_up"] = (df["rsi"] / 100) * 100

else:

    model = RandomForestClassifier(
        n_estimators=80,
        max_depth=8,
        random_state=42
    )

    model.fit(X, y)

    df["ml_signal"] = model.predict(X)
    df["ml_prob_up"] = model.predict_proba(X)[:, 1] * 100

# ======================
# SAFE FINAL
# ======================
df["ml_signal"] = df["ml_signal"].ffill().fillna(0)
df["ml_prob_up"] = df["ml_prob_up"].ffill().fillna(50)

# ======================
# OUTPUT SICURO
# ======================
if "ml_prob_up" in df.columns and len(df["ml_prob_up"].dropna()) > 0:
    up = float(df["ml_prob_up"].dropna().iloc[-1])
else:
    up = 50.0
signal = int(df["ml_signal"].iloc[-1])

st.metric("📈 Probabilità salita", f"{up:.1f}%")
st.metric("🎯 Segnale", "BUY" if signal == 1 else "SELL")

# ======================
# SIMULATORE
# ======================
capital = 1000
position = 0
equity = []

for i in range(len(df)):
    price = df["close"].iloc[i]
    sig = df["ml_signal"].iloc[i]

    if sig == 1 and position == 0:
        position = capital / price
        capital = 0

    elif sig == 0 and position > 0:
        capital = position * price
        position = 0

    total = capital if position == 0 else position * price
    equity.append(total)

df["equity"] = equity

# ======================
# GRAFICO
# ======================
fig = go.Figure()

fig.add_trace(go.Candlestick(
    x=df["time"],
    open=df["open"],
    high=df["high"],
    low=df["low"],
    close=df["close"]
))

buy = df[df["ml_signal"] == 1]
sell = df[df["ml_signal"] == 0]

fig.add_trace(go.Scatter(
    x=buy["time"],
    y=buy["low"] * 0.999,
    mode="markers",
    marker=dict(symbol="triangle-up", color="green", size=10),
    name="BUY"
))

fig.add_trace(go.Scatter(
    x=sell["time"],
    y=sell["high"] * 1.001,
    mode="markers",
    marker=dict(symbol="triangle-down", color="red", size=10),
    name="SELL"
))

fig.update_layout(xaxis_rangeslider_visible=False)

st.plotly_chart(fig, use_container_width=True)

# ======================
# EQUITY
# ======================
st.subheader("💰 Capitale simulato")
st.line_chart(df["equity"])
