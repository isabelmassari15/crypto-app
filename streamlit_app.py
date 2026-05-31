import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
import ta
from sklearn.ensemble import RandomForestClassifier

st.set_page_config(layout="wide")
st.title("🧠 STREAMLIT PRO TRADING ENGINE")

# =========================
# INPUT
# =========================
asset = st.selectbox("Asset", ["BTCUSDT", "ETHUSDT", "GOLD"])
timeframe = st.selectbox("Timeframe", ["15m", "30m", "1h"], index=0)
capital = st.sidebar.number_input("💰 Capitale simulato", value=1000)

# =========================
# DATA FETCH SAFE
# =========================
def get_data(symbol):
    try:
        if symbol == "GOLD":
            url = "https://stooq.com/q/d/l/?s=xauusd&i=60"
            df = pd.read_csv(url)
            df.columns = [c.lower() for c in df.columns]
            df["date"] = pd.to_datetime(df["date"])
            df = df.rename(columns={"date":"time"})
        else:
            url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={timeframe}&limit=1000"
            r = requests.get(url, timeout=10)
            data = r.json()

            if not isinstance(data, list):
                return pd.DataFrame()

            df = pd.DataFrame(data, columns=[
                "time","open","high","low","close","volume",
                "c1","c2","c3","c4","c5","c6"
            ])

            df["time"] = pd.to_datetime(df["time"], unit="ms")

        for c in ["open","high","low","close"]:
            df[c] = pd.to_numeric(df[c], errors="coerce")

        return df.dropna()

    except:
        return pd.DataFrame()

df = get_data(asset)

# =========================
# SAFETY CHECK
# =========================
if df.empty or len(df) < 80:
    st.warning("⚠️ Dati insufficienti → attendo refresh")
    st.stop()

# =========================
# INDICATORS
# =========================
df["ma10"] = df["close"].rolling(10).mean()
df["ma20"] = df["close"].rolling(20).mean()

df["rsi"] = ta.momentum.RSIIndicator(df["close"]).rsi()

macd = ta.trend.MACD(df["close"])
df["macd"] = macd.macd()
df["macd_signal"] = macd.macd_signal()

# =========================
# ML TARGET
# =========================
df["future"] = df["close"].shift(-1)
df["target"] = (df["future"] > df["close"]).astype(int)

features = ["ma10","ma20","rsi","macd","macd_signal"]

df_ml = df[features + ["target"]].ffill().bfill().dropna()

df["signal"] = 0
df["prob"] = 50

# =========================
# MODEL STABILE
# =========================
if len(df_ml) > 100:

    model = RandomForestClassifier(
        n_estimators=120,
        max_depth=6,
        random_state=42
    )

    model.fit(df_ml[features], df_ml["target"])

    df["signal"] = model.predict(df_ml[features])
    df["prob"] = model.predict_proba(df_ml[features])[:, 1] * 100

else:
    df["signal"] = (df["ma10"] > df["ma20"]).astype(int)
    df["prob"] = df["rsi"].fillna(50)

df = df.dropna()

# =========================
# LAST VALUES
# =========================
last_signal = int(df["signal"].iloc[-1])
last_prob = float(df["prob"].iloc[-1])

# =========================
# DASHBOARD
# =========================
col1, col2, col3 = st.columns(3)

col1.metric("📈 Probabilità", f"{last_prob:.1f}%")
col2.metric("📊 Segnale", "🟢 BUY" if last_signal == 1 else "🔴 SELL")
col3.metric("💰 Capitale", f"{capital}$")

# =========================
# SIMULAZIONE
# =========================
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

# =========================
# CANDLE CHART + SIGNALS
# =========================
fig = go.Figure()

fig.add_trace(go.Candlestick(
    x=df["time"],
    open=df["open"],
    high=df["high"],
    low=df["low"],
    close=df["close"],
    name="Price"
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

# =========================
# EQUITY
# =========================
st.subheader("📊 Portfolio simulato")
st.line_chart(df["equity"])

# =========================
# LEGGENDA PRO
# =========================
st.markdown("""
## 📘 STREAMLIT PRO LEGEND

🟢 BUY → trend rialzista + momentum positivo  
🔴 SELL → trend ribassista + perdita momentum  

📊 Probabilità → forza AI (0–100%)  
💰 Equity → simulazione capitale reale  
🕯️ Candele → mercato reale  

⚠️ Nessun sistema predice il mercato al 100%
""")
