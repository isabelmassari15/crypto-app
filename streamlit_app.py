import streamlit as st
import pandas as pd
import requests
import ta
import plotly.graph_objects as go

st.set_page_config(layout="wide")

st.title("🚀 CRYPTO AI BOT PRO")

# ===== SCELTA ASSET =====
symbol = st.selectbox("Scegli Crypto", ["BTCUSDT", "ETHUSDT"])

# ===== DATI (CoinGecko) =====
coin_id = "bitcoin" if symbol == "BTCUSDT" else "ethereum"
from binance.client import Client

client = Client("", "")  # senza API = solo dati

klines = client.get_klines(symbol=symbol, interval="1m", limit=200)

df = pd.DataFrame(klines, columns=[
    "time","open","high","low","close","volume",
    "close_time","qav","num_trades","taker_base","taker_quote","ignore"
])

df["close"] = df["close"].astype(float)

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

# ===== SCORE =====
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

# ===== GRAFICO =====
fig = go.Figure()

fig.add_trace(go.Scatter(y=df["close"], name="Prezzo"))
fig.add_trace(go.Scatter(y=df["ma20"], name="MA20"))
fig.add_trace(go.Scatter(y=df["ma50"], name="MA50"))

st.plotly_chart(fig, use_container_width=True)

# ===== OUTPUT =====
last_signal = df["signal"].iloc[-1]
last_score = df["score"].iloc[-1]

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
- **STRONG BUY** → Alta probabilità salita (trend + momentum forti)
- **BUY** → Buon momento per entrare ma non perfetto
- **HOLD** → Mercato incerto
- **SELL** → Possibile discesa
- **STRONG SELL** → Alta probabilità discesa

⚠️ ATTENZIONE:
- Nessun sistema è sicuro al 100%
- Usa sempre gestione del rischio
""")

# ===== BINANCE MANUALE =====
st.subheader("💰 Trading Manuale (Opzionale)")

api_key = st.text_input("API KEY Binance")
api_secret = st.text_input("API SECRET Binance", type="password")

if st.button("🟢 Compra"):
    st.info("Ordine simulato (collega Binance per reale)")

if st.button("🔴 Vendi"):
    st.info("Ordine simulato (collega Binance per reale)")
