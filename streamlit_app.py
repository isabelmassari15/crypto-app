import streamlit as st
import pandas as pd
import requests
import ta
import plotly.graph_objects as go
import numpy as np
from sklearn.ensemble import RandomForestClassifier

st.set_page_config(layout="wide")

st.title("🧠 AI TRADING BOT PRO — FINAL STABLE")

# ======================
# INPUT
# ======================
asset = st.selectbox("Asset", ["BTCUSDT", "ETHUSDT"])
timeframe = st.selectbox("Timeframe", ["1m", "5m", "15m", "30m", "1h"])

# ======================
# DATA BINANCE
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
# INDICATORI
# ======================
df["ma10"] = df["close"].rolling(10).mean()
df["ma20"] = df["close"].rolling(20).mean()

df["rsi"] = ta.momentum.RSIIndicator(df["close"], window=14).rsi()

macd = ta.trend.MACD(df["close"])
df["macd"] = macd.macd()
df["macd_signal"] = macd.macd_signal()

# target
df["future"] = df["close"].shift(-1)
df["target"] = (df["future"] > df["close"]).astype(int)

features = ["ma10", "ma20", "rsi", "macd", "macd_signal"]

# ======================
# DATASET ML
# ======================
df_ml = df[features + ["target"]].copy()
df_ml = df_ml.replace([np.inf, -np.inf], np.nan)
df_ml = df_ml.ffill().bfill()

df["ml_signal"] = np.nan
df["ml_prob_up"] = np.nan

# ======================
# MODEL
# ======================
if len(df_ml) < 100:

    # fallback intelligente
    df["ml_signal"] = (df["ma10"] > df["ma20"]).astype(int)
    df["ml_prob_up"] = df["rsi"].fillna(50)

    st.warning("⚠️ Modalità fallback (dati limitati)")

else:

    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=8,
        random_state=42
    )

    model.fit(df_ml[features], df_ml["target"])

    df["ml_signal"] = model.predict(df_ml[features])
    df["ml_prob_up"] = model.predict_proba(df_ml[features])[:, 1] * 100

# ======================
# CLEAN FINAL
# ======================
df["ml_signal"] = df["ml_signal"].ffill().fillna(0)
df["ml_prob_up"] = df["ml_prob_up"].ffill().fillna(50)

# ======================
# OUTPUT SICURO
# ======================
valid = df.dropna(subset=["ml_prob_up", "ml_signal"])

last_prob = float(valid["ml_prob_up"].iloc[-1]) if len(valid) > 0 else 50
last_signal = int(valid["ml_signal"].iloc[-1]) if len(valid) > 0 else 0

# ======================
# DASHBOARD
# ======================
col1, col2, col3 = st.columns(3)

col1.metric("📈 Probabilità salita", f"{last_prob:.1f}%")
col2.metric("📊 Segnale", "🟢 BUY" if last_signal == 1 else "🔴 SELL")
col3.metric("⚡ Forza", "FORTE" if abs(last_prob - 50) > 20 else "DEBOLE")

# ======================
# GRAFICO
# ======================
fig = go.Figure()

fig.add_trace(go.Candlestick(
    x=df["time"],
    open=df["open"],
    high=df["high"],
    low=df["low"],
    close=df["close"],
    name="Price"
))

buy = df[df["ml_signal"] == 1]
sell = df[df["ml_signal"] == 0]

fig.add_trace(go.Scatter(
    x=buy["time"],
    y=buy["low"] * 0.998,
    mode="markers+text",
    marker=dict(symbol="triangle-up", color="green", size=12),
    text=["BUY"] * len(buy),
    textposition="top center",
    name="BUY"
))

fig.add_trace(go.Scatter(
    x=sell["time"],
    y=sell["high"] * 1.002,
    mode="markers+text",
    marker=dict(symbol="triangle-down", color="red", size=12),
    text=["SELL"] * len(sell),
    textposition="bottom center",
    name="SELL"
))

fig.update_layout(
    height=700,
    xaxis_rangeslider_visible=False,
    title="📊 AI Trading Bot — BUY / SELL Signals"
)

st.plotly_chart(fig, use_container_width=True)

# ======================
# LEGGENDA
# ======================
st.markdown("""
## 📘 Legenda

🟢 BUY → previsione salita  
🔴 SELL → previsione discesa  

📈 50% = neutro  
📈 >70% = forte BUY  
📉 <30% = forte SELL  

⚡ Forza = sicurezza AI
""")
