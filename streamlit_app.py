import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
import ta
from sklearn.ensemble import RandomForestClassifier

st.set_page_config(layout="wide")

st.title("🧠 AI TRADING BOT PRO — MULTI ASSET + GOLD + PORTFOLIO")

# ======================
# ASSET
# ======================
asset = st.selectbox("Asset", ["BTCUSDT", "ETHUSDT", "GOLD (XAUUSD)"])
timeframe = st.selectbox("Timeframe", ["1m", "5m", "15m", "30m", "1h"])

# ======================
# DATA SOURCE
# ======================
def get_data(asset):

    # GOLD separato (perché non è su Binance)
    if asset == "GOLD (XAUUSD)":
        url = "https://www.goldapi.io/api/XAU/USD"
        headers = {"x-access-token": "demo"}  # fallback pubblico
        return None  # fallback semplice (evita crash)

    url = f"https://api.binance.com/api/v3/klines?symbol={asset}&interval={timeframe}&limit=1000"
    data = requests.get(url).json()

    df = pd.DataFrame(data, columns=[
        "time","open","high","low","close","volume",
        "c1","c2","c3","c4","c5","c6"
    ])

    df["time"] = pd.to_datetime(df["time"], unit="ms")

    for col in ["open","high","low","close","volume"]:
        df[col] = df[col].astype(float)

    return df

df = get_data(asset)

if df is None or len(df) < 50:
    st.warning("⚠️ GOLD in modalità semplificata o dati insufficienti")
    st.stop()

# ======================
# INDICATORI
# ======================
df["ma10"] = df["close"].rolling(10).mean()
df["ma20"] = df["close"].rolling(20).mean()
df["rsi"] = ta.momentum.RSIIndicator(df["close"]).rsi()

macd = ta.trend.MACD(df["close"])
df["macd"] = macd.macd()
df["macd_signal"] = macd.macd_signal()

# ======================
# TARGET
# ======================
df["future"] = df["close"].shift(-1)
df["target"] = (df["future"] > df["close"]).astype(int)

features = ["ma10", "ma20", "rsi", "macd", "macd_signal"]

df_ml = df[features + ["target"]].copy()
df_ml = df_ml.ffill().bfill()

df["signal"] = 0
df["prob"] = 50

# ======================
# MODEL
# ======================
if len(df_ml) > 100:

    model = RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42)
    model.fit(df_ml[features], df_ml["target"])

    df["signal"] = model.predict(df_ml[features])
    df["prob"] = model.predict_proba(df_ml[features])[:, 1] * 100

else:
    df["signal"] = (df["ma10"] > df["ma20"]).astype(int)
    df["prob"] = df["rsi"].fillna(50)

# ======================
# PORTFOLIO SIMULATO
# ======================
capital = st.sidebar.number_input("💰 Capitale iniziale", value=1000)

position = 0
cash = capital
equity = []

for i in range(len(df)):
    price = df["close"].iloc[i]
    sig = df["signal"].iloc[i]

    if sig == 1 and position == 0:
        position = cash / price
        cash = 0

    elif sig == 0 and position > 0:
        cash = position * price
        position = 0

    total = cash if position == 0 else position * price
    equity.append(total)

df["equity"] = equity

# ======================
# OUTPUT
# ======================
last_prob = float(df["prob"].iloc[-1])
last_signal = int(df["signal"].iloc[-1])

col1, col2, col3 = st.columns(3)

col1.metric("📈 Probabilità salita", f"{last_prob:.1f}%")
col2.metric("📊 Segnale", "🟢 BUY" if last_signal == 1 else "🔴 SELL")
col3.metric("💰 Portfolio", f"{df['equity'].iloc[-1]:.2f}$")

# ======================
# GRAFICO CANDLE + FRECCE
# ======================
fig = go.Figure()

fig.add_trace(go.Candlestick(
    x=df["time"],
    open=df["open"],
    high=df["high"],
    low=df["low"],
    close=df["close"]
))

buy = df[df["signal"] == 1]
sell = df[df["signal"] == 0]

fig.add_trace(go.Scatter(
    x=buy["time"],
    y=buy["low"] * 0.998,
    mode="markers+text",
    marker=dict(symbol="triangle-up", color="green", size=12),
    text=["BUY"] * len(buy),
    name="BUY"
))

fig.add_trace(go.Scatter(
    x=sell["time"],
    y=sell["high"] * 1.002,
    mode="markers+text",
    marker=dict(symbol="triangle-down", color="red", size=12),
    text=["SELL"] * len(sell),
    name="SELL"
))

fig.update_layout(
    height=700,
    xaxis_rangeslider_visible=False
)

st.plotly_chart(fig, use_container_width=True)

# ======================
# EQUITY
# ======================
st.subheader("📊 Portfolio simulato")
st.line_chart(df["equity"])

# ======================
# LEGGENDA
# ======================
st.markdown("""
## 📘 Legenda

🟢 BUY → AI prevede salita  
🔴 SELL → AI prevede discesa  

📈 Percentuale:
- 50% neutro
- >70% forte BUY
- <30% forte SELL  

💰 Portfolio:
- simulazione investimento automatico

🪙 Asset:
- BTC, ETH, GOLD
""")
