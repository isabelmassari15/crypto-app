import streamlit as st
import pandas as pd
import requests
import ta
import plotly.graph_objects as go
import time

st.set_page_config(layout="wide")

st.title("🚀 CRYPTO AI BOT PRO LIVE")

# ===== AUTO REFRESH =====
st.caption("Aggiornamento automatico ogni 10 secondi")
time.sleep(1)

# ===== SCELTA ASSET =====
symbol = st.selectbox("Scegli Crypto", ["BTCUSDT", "ETHUSDT"])

# ===== DATI REALI BINANCE =====
url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1m&limit=200"
data = requests.get(url).json()

df = pd.DataFrame(data, columns=[
    "time","open","high","low","close","volume",
    "close_time","qav","num_trades","taker_base","taker_quote","ignore"
])

df["close"] = df["close"].astype(float)

# ===== PREZZO LIVE =====
ticker_url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
price_data = requests.get(ticker_url).json()

if "price" in price_data:
    live_price = float(price_data["price"])
else:
    st.error("Errore nel recupero prezzo Binance")
    st.write(price_data)
    live_price = df["close"].iloc[-1]  # fallback

st.metric("💰 Prezzo LIVE", f"{live_price:.2f} $")

# ===== INDICATORI =====
df["ma20"] = df["close"].rolling(20).mean()
df["ma50"] = df["close"].rolling(50).mean()
df["rsi"] = ta.momentum.RSIIndicator(df["close"]).rsi()

macd = ta.trend.MACD(df["close"])
df["macd"] = macd.macd()
df["macd_signal"] = macd.macd_signal()

bb = ta.volatility.BollingerBands(df["close"])
df["bb_high"] = bb.bollinger_hband()
df["bb_low"] = bb.bollinger_lband()

# ===== SCORE AI =====
df["score"] = 0

df.loc[df["ma20"] > df["ma50"], "score"] += 2
df.loc[df["ma20"] < df["ma50"], "score"] -= 2

df.loc[df["rsi"] < 30, "score"] += 2
df.loc[df["rsi"] > 70, "score"] -= 2

df.loc[df["macd"] > df["macd_signal"], "score"] += 1
df.loc[df["macd"] < df["macd_signal"], "score"] -= 1

df.loc[df["close"] < df["bb_low"], "score"] += 1
df.loc[df["close"] > df["bb_high"], "score"] -= 1

# ===== SEGNALE =====
def get_signal(score):
    if score >= 4:
        return "STRONG BUY"
    elif score >= 2:
        return "BUY"
    elif score == 0:
        return "HOLD"
    elif score <= -4:
        return "STRONG SELL"
    else:
        return "SELL"

df["signal"] = df["score"].apply(get_signal)

# ===== ULTIMO SEGNALE =====
last_signal = df["signal"].iloc[-1]
last_score = df["score"].iloc[-1]

# ===== GRAFICO =====
fig = go.Figure()

fig.add_trace(go.Scatter(y=df["close"], name="Prezzo"))
fig.add_trace(go.Scatter(y=df["ma20"], name="MA20"))
fig.add_trace(go.Scatter(y=df["ma50"], name="MA50"))

# FRECCE BUY/SELL
buy_signals = df[df["signal"].str.contains("BUY")]
sell_signals = df[df["signal"].str.contains("SELL")]

fig.add_trace(go.Scatter(
    x=buy_signals.index,
    y=buy_signals["close"],
    mode="markers",
    name="BUY",
    marker=dict(symbol="triangle-up", size=10)
))

fig.add_trace(go.Scatter(
    x=sell_signals.index,
    y=sell_signals["close"],
    mode="markers",
    name="SELL",
    marker=dict(symbol="triangle-down", size=10)
))

st.plotly_chart(fig, use_container_width=True)

# ===== OUTPUT =====
st.subheader("📊 ANALISI AI")

col1, col2 = st.columns(2)

with col1:
    st.metric("Segnale", last_signal)

with col2:
    st.metric("Forza", f"{last_score}/6")

if "BUY" in last_signal:
    st.success(last_signal)
elif "SELL" in last_signal:
    st.error(last_signal)
else:
    st.warning("HOLD")

# ===== LEGENDA =====
st.subheader("📘 LEGENDA")

st.markdown("""
- **STRONG BUY** → forte probabilità salita
- **BUY** → buona opportunità
- **HOLD** → mercato incerto
- **SELL** → possibile discesa
- **STRONG SELL** → forte probabilità discesa

Indicatori usati:
- MA20/MA50 → trend
- RSI → ipercomprato/ipervenduto
- MACD → momentum
- Bollinger → volatilità

⚠️ Nessun bot è sicuro al 100%
""")
