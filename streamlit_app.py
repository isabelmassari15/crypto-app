import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
import ta
from sklearn.ensemble import RandomForestClassifier

st.set_page_config(layout="wide")

st.title("🧠 AI TRADING BOT PRO — FIXED ARCHITECTURE")

# ======================
# ASSETS SEPARATI
# ======================
asset = st.selectbox("Asset", ["BTCUSDT", "ETHUSDT", "GOLD"])

timeframe = st.selectbox("Timeframe", ["1m", "5m", "15m", "30m", "1h"])

# ======================
# DATA FUNCTIONS (SEPARATE)
# ======================
def get_crypto(symbol):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={timeframe}&limit=1000"
    data = requests.get(url).json()

    df = pd.DataFrame(data, columns=[
        "time","open","high","low","close","volume",
        "c1","c2","c3","c4","c5","c6"
    ])

    df["time"] = pd.to_datetime(df["time"], unit="ms")

    for c in ["open","high","low","close"]:
        df[c] = df[c].astype(float)

    return df


def get_gold():
    # fallback vero (Yahoo finance proxy pubblico)
    url = "https://query1.finance.yahoo.com/v8/finance/chart/XAUUSD=X?interval=15m&range=7d"
    r = requests.get(url).json()

    try:
        t = r["chart"]["result"][0]["timestamp"]
        o = r["chart"]["result"][0]["indicators"]["quote"][0]

        df = pd.DataFrame({
            "time": pd.to_datetime(t, unit="s"),
            "open": o["open"],
            "high": o["high"],
            "low": o["low"],
            "close": o["close"]
        })

        df = df.dropna()
        return df

    except:
        return pd.DataFrame()


# ======================
# SELECT DATA
# ======================
if asset in ["BTCUSDT", "ETHUSDT"]:
    df = get_crypto(asset)
else:
    df = get_gold()

# ======================
# SAFETY CHECK (IMPORTANTISSIMO)
# ======================
if df is None or len(df) < 50:
    st.error("❌ Dati insufficienti per questo asset/timeframe")
    st.stop()

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

df_ml = df[features + ["target"]].ffill().bfill()

# ======================
# MODEL SAFE
# ======================
df["signal"] = 0
df["prob"] = 50

if len(df_ml) > 80:

    model = RandomForestClassifier(n_estimators=80, max_depth=6)
    model.fit(df_ml[features], df_ml["target"])

    df["signal"] = model.predict(df_ml[features])
    df["prob"] = model.predict_proba(df_ml[features])[:, 1] * 100

else:
    df["signal"] = (df["ma10"] > df["ma20"]).astype(int)
    df["prob"] = df["rsi"].fillna(50)

# ======================
# OUTPUT SAFE
# ======================
last_prob = float(df["prob"].dropna().iloc[-1])
last_signal = int(df["signal"].dropna().iloc[-1])

col1, col2 = st.columns(2)
col1.metric("📈 Probabilità", f"{last_prob:.1f}%")
col2.metric("📊 Segnale", "🟢 BUY" if last_signal == 1 else "🔴 SELL")

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

buy = df[df["signal"] == 1]
sell = df[df["signal"] == 0]

fig.add_trace(go.Scatter(
    x=buy["time"],
    y=buy["low"],
    mode="markers",
    marker=dict(color="green", size=10, symbol="triangle-up"),
    name="BUY"
))

fig.add_trace(go.Scatter(
    x=sell["time"],
    y=sell["high"],
    mode="markers",
    marker=dict(color="red", size=10, symbol="triangle-down"),
    name="SELL"
))

fig.update_layout(height=650, xaxis_rangeslider_visible=False)

st.plotly_chart(fig, use_container_width=True)

# ======================
# LEGGENDA
# ======================
st.markdown("""
## 📘 Legenda

🟢 BUY → salita probabile  
🔴 SELL → discesa probabile  

🪙 BTC/ETH → Binance  
🥇 GOLD → Yahoo Finance  

⚠️ Se dati insufficienti → blocco automatico
""")
