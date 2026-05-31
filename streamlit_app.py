import streamlit as st
import pandas as pd
import requests
import ta
import plotly.graph_objects as go
import numpy as np
from sklearn.ensemble import RandomForestClassifier

st.set_page_config(layout="wide")

st.title("🧠 AI TRADING BOT PRO — ULTRA STABLE V2")

# ======================
# INPUT
# ======================
asset = st.selectbox("Asset", ["BTCUSDT", "ETHUSDT"])
timeframe = st.selectbox("Timeframe", ["1m", "5m", "15m", "30m", "1h"])

# ======================
# DATA
# ======================
url = f"https://api.binance.com/api/v3/klines?symbol={asset}&interval={timeframe}&limit=800"
data = requests.get(url).json()

df = pd.DataFrame(data, columns=[
    "time","open","high","low","close","volume",
    "c1","c2","c3","c4","c5","c6"
])

df["time"] = pd.to_datetime(df["time"], unit="ms")

for col in ["open","high","low","close","volume"]:
    df[col] = df[col].astype(float)

# ======================
# INDICATORS
# ======================
df["ma10"] = df["close"].rolling(10).mean()
df["ma20"] = df["close"].rolling(20).mean()

df["rsi"] = ta.momentum.RSIIndicator(df["close"]).rsi()

macd = ta.trend.MACD(df["close"])
df["macd"] = macd.macd()
df["macd_signal"] = macd.macd_signal()

df["future"] = df["close"].shift(-1)
df["target"] = (df["future"] > df["close"]).astype(int)

features = ["ma10", "ma20", "rsi", "macd", "macd_signal"]

# ======================
# ML DATASET
# ======================
df_ml = df[features + ["target"]].copy()
df_ml = df_ml.replace([np.inf, -np.inf], np.nan).dropna()

df["ml_signal"] = np.nan
df["ml_prob_up"] = np.nan

# ======================
# MODEL / FALLBACK
# ======================
if len(df_ml) < 60:

    st.warning("⚠️ Fallback attivo (dati insufficienti)")

    df["ml_signal"] = (df["ma10"] > df["ma20"]).astype(int)
    df["ml_prob_up"] = df["ml_signal"] * 100

else:

    X = df_ml[features]
    y = df_ml["target"]

    model = RandomForestClassifier(
        n_estimators=60,
        random_state=42
    )

    model.fit(X, y)

    df.loc[df_ml.index, "ml_signal"] = model.predict(X)
    df.loc[df_ml.index, "ml_prob_up"] = model.predict_proba(X)[:, 1] * 100

# ======================
# SAFE FILL (IMPORTANTE)
# ======================
df["ml_signal"] = df["ml_signal"].ffill().fillna(0)
df["ml_prob_up"] = df["ml_prob_up"].ffill().fillna(50)

# ======================
# SAFE OUTPUT (NO CRASH MAI)
# ======================
valid_prob = df["ml_prob_up"].dropna()
valid_sig = df["ml_signal"].dropna()

if len(valid_prob) == 0:
    up = 50
else:
    up = float(valid_prob.iloc[-1])

if len(valid_sig) == 0:
    signal = 0
else:
    signal = int(valid_sig.iloc[-1])

# safety finale
if np.isnan(up):
    up = 50
if np.isnan(signal):
    signal = 0

st.metric("📈 Probabilità salita", f"{up:.1f}%")
st.metric("🎯 Segnale", "BUY" if signal == 1 else "SELL")

# ======================
# SIMULATOR
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
# CHART
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
st.subheader("💰 Capitale simulato")
st.line_chart(df["equity"])

# ======================
# LEGGENDA
# ======================
st.subheader("📘 Legenda")

st.markdown("""
🧠 AI:
- ML se possibile
- fallback se dati insufficienti
- sempre output stabile

📊 Segnali:
- BUY = trend positivo
- SELL = trend negativo

💰 Simulatore:
- trading virtuale automatico

⚠️ NON è consulenza finanziaria
""")
