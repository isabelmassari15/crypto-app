import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
import ta
from sklearn.ensemble import RandomForestClassifier

# ======================
# AUTO REFRESH
# ======================
st.set_page_config(layout="wide")
st.title("🧠 AI TRADING BOT PRO — STABLE LIVE")

st.markdown("🔄 Auto-refresh attivo (10s)")
st_autorefresh = st.empty()

# ======================
# INPUT
# ======================
asset = st.selectbox("Asset", ["BTCUSDT", "ETHUSDT"])
timeframe = st.selectbox("Timeframe", ["15m", "30m", "1h"], index=0)

capital = st.sidebar.number_input("💰 Capitale simulato", value=1000)

# ======================
# DATA
# ======================
def get_data(symbol):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={timeframe}&limit=1000"
    data = requests.get(url).json()

    df = pd.DataFrame(data, columns=[
        "time","open","high","low","close","volume",
        "c1","c2","c3","c4","c5","c6"
    ])

    df["time"] = pd.to_datetime(df["time"], unit="ms")

    for col in ["open","high","low","close"]:
        df[col] = df[col].astype(float)

    return df

df = get_data(asset)

# ======================
# SAFETY CHECK
# ======================
if df is None or len(df) < 120:
    st.error("❌ Dati insufficienti anche su timeframe stabile")
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

# ======================
# TARGET ML
# ======================
df["future"] = df["close"].shift(-1)
df["target"] = (df["future"] > df["close"]).astype(int)

features = ["ma10", "ma20", "rsi", "macd", "macd_signal"]

df_ml = df[features + ["target"]].copy()
df_ml = df_ml.ffill().bfill()

df["signal"] = 0
df["prob"] = 50

# ======================
# MODEL SAFE
# ======================
if len(df_ml) > 120:

    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=6,
        random_state=42
    )

    model.fit(df_ml[features], df_ml["target"])

    df["signal"] = model.predict(df_ml[features])
    df["prob"] = model.predict_proba(df_ml[features])[:, 1] * 100

else:
    df["signal"] = (df["ma10"] > df["ma20"]).astype(int)
    df["prob"] = df["rsi"].fillna(50)

# ======================
# SAFE FINAL VALUES
# ======================
df = df.dropna()

last_prob = float(df["prob"].iloc[-1])
last_signal = int(df["signal"].iloc[-1])

# ======================
# SIMULAZIONE TRADING
# ======================
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
# DASHBOARD
# ======================
col1, col2, col3 = st.columns(3)

col1.metric("📈 Probabilità salita", f"{last_prob:.1f}%")
col2.metric("📊 Segnale", "🟢 BUY" if last_signal == 1 else "🔴 SELL")
col3.metric("💰 Portfolio", f"{df['equity'].iloc[-1]:.2f}$")

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

# ======================
# EQUITY
# ======================
st.subheader("📊 Simulazione investimento")
st.line_chart(df["equity"])

# ======================
# LEGGENDA
# ======================
st.markdown("""
## 📘 Legenda

🟢 BUY → previsione salita  
🔴 SELL → previsione discesa  

📊 Timeframe consigliato:
- 15m = stabile
- 30m = più preciso
- 1h = più affidabile

🔄 Auto-refresh ogni 10 secondi
""")
