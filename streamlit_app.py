import streamlit as st
import pandas as pd
import requests
import ta
import plotly.graph_objects as go
import numpy as np

st.set_page_config(layout="wide")

st.title("🧠 AI TRADING BOT PRO (ULTIMATE STABLE)")

# ======================
# INPUT
# ======================
asset = st.selectbox("Asset", ["BTCUSDT", "ETHUSDT"])
timeframe = st.selectbox("Timeframe", ["1m", "5m", "15m", "30m", "1h"])

# ======================
# DATA BINANCE
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
# INDICATORI
# ======================
df["ma10"] = df["close"].rolling(10).mean()
df["ma20"] = df["close"].rolling(20).mean()
df["rsi"] = ta.momentum.RSIIndicator(df["close"]).rsi()

macd = ta.trend.MACD(df["close"])
df["macd"] = macd.macd()
df["macd_signal"] = macd.macd_signal()

df = df.replace([np.inf, -np.inf], np.nan)

# ======================
# TARGET
# ======================
df["future"] = df["close"].shift(-1)
df["target"] = (df["future"] > df["close"]).astype(int)

features = ["ma10", "ma20", "rsi", "macd", "macd_signal"]

df_clean = df[features + ["target"]].dropna()

X = df_clean[features]
y = df_clean["target"]

# ======================
# ML O FALLBACK
# ======================
if len(df_clean) < 80:

    st.warning("⚠️ Dataset piccolo → modalità fallback attiva")

    df["ml_signal"] = (df["ma10"] > df["ma20"]).astype(int)
    df["ml_prob_up"] = df["ml_signal"] * 100

else:
    from sklearn.ensemble import RandomForestClassifier

    model = RandomForestClassifier(
        n_estimators=60,
        random_state=42
    )

    model.fit(X, y)

    df.loc[df_clean.index, "ml_signal"] = model.predict(X)
    df.loc[df_clean.index, "ml_prob_up"] = model.predict_proba(X)[:, 1] * 100

# ======================
# PULIZIA SOLO PER ML
# ======================
df = df.replace([np.inf, -np.inf], np.nan)

# ======================
# ML O FALLBACK
# ======================
if len(df_clean) < 80:

    st.warning("⚠️ Dataset piccolo → fallback attivo")

    df["ml_signal"] = (df["ma10"] > df["ma20"]).astype(int)

    df["ml_prob_up"] = df["ml_signal"] * 100

else:
    from sklearn.ensemble import RandomForestClassifier

    model = RandomForestClassifier(
        n_estimators=60,
        random_state=42
    )

    model.fit(X, y)

    df.loc[df_clean.index, "ml_signal"] = model.predict(X)
    df.loc[df_clean.index, "ml_prob_up"] = model.predict_proba(X)[:, 1] * 100


# ======================
# SICUREZZA FINALE (FIX CRASH)
# ======================
df = df.dropna(subset=["ml_signal", "ml_prob_up"])

if len(df) == 0:
    st.error("❌ Nessun dato valido per mostrare segnali")
    st.stop()

# ======================
# OUTPUT SICURO
# ======================
up = df["ml_prob_up"].iloc[-1]
signal = df["ml_signal"].iloc[-1]

# ======================
# OUTPUT
# ======================
up = df["ml_prob_up"].iloc[-1]
signal = df["ml_signal"].iloc[-1]

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
🧠 AI BOT:
- usa ML se dati sufficienti
- fallback semplice se dati pochi

📊 Segnali:
- BUY = trend positivo
- SELL = trend negativo

💰 Simulatore:
- compra/vende automaticamente virtuale

⚠️ Non è consulenza finanziaria
""")
