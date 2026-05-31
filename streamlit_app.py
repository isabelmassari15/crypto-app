import streamlit as st
import pandas as pd
import requests
import ta
import plotly.graph_objects as go

st.set_page_config(layout="wide")

st.title("🚀 Crypto AI Bot (Stable Version)")

# ======================
# SCELTA CRYPTO
# ======================
symbol = st.selectbox("Scegli Crypto", ["BTC", "ETH"])

coin_map = {
    "BTC": "bitcoin",
    "ETH": "ethereum"
}

coin_id = coin_map[symbol]

# ======================
# PREZZO LIVE
# ======================
price_url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
price_data = requests.get(price_url).json()

live_price = price_data[coin_id]["usd"]

st.metric("💰 Prezzo LIVE", f"{live_price:.2f} $")

# ======================
# DATI STORICI
# ======================
chart_url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days=7"
data = requests.get(chart_url).json()

prices = data["prices"]

df = pd.DataFrame(prices, columns=["time", "close"])

df["time"] = pd.to_datetime(df["time"], unit="ms")
df["close"] = df["close"].astype(float)

# sicurezza
if df.empty:
    st.error("Nessun dato disponibile")
    st.stop()

# ======================
# INDICATORI
# ======================
df["ma20"] = df["close"].rolling(20).mean()
df["ma50"] = df["close"].rolling(50).mean()

df["rsi"] = ta.momentum.RSIIndicator(df["close"]).rsi()

macd = ta.trend.MACD(df["close"])
df["macd"] = macd.macd()
df["macd_signal"] = macd.macd_signal()

# ======================
# SCORE AI
# ======================
df["score"] = 0

df.loc[df["ma20"] > df["ma50"], "score"] += 1
df.loc[df["ma20"] < df["ma50"], "score"] -= 1

df.loc[df["rsi"] < 30, "score"] += 1
df.loc[df["rsi"] > 70, "score"] -= 1

df.loc[df["macd"] > df["macd_signal"], "score"] += 1
df.loc[df["macd"] < df["macd_signal"], "score"] -= 1

# ======================
# SEGNALE FINALE
# ======================
def get_signal(score):
    if score >= 2:
        return "🟢 BUY"
    elif score <= -2:
        return "🔴 SELL"
    else:
        return "🟡 HOLD"

df["signal"] = df["score"].apply(get_signal)

last_signal = df["signal"].iloc[-1]
last_score = df["score"].iloc[-1]

# ======================
# DASHBOARD
# ======================
st.subheader("📊 Segnale AI")

col1, col2 = st.columns(2)

with col1:
    st.metric("Segnale", last_signal)

with col2:
    st.metric("Score", int(last_score))

# ======================
# GRAFICO
# ======================
fig = go.Figure()

fig.add_trace(go.Scatter(y=df["close"], name="Prezzo"))
fig.add_trace(go.Scatter(y=df["ma20"], name="MA20"))
fig.add_trace(go.Scatter(y=df["ma50"], name="MA50"))

st.plotly_chart(fig, use_container_width=True)

# ======================
# LEGENDA
# ======================
st.subheader("📘 Legenda")

st.markdown("""
- 🟢 **BUY** → possibile salita
- 🔴 **SELL** → possibile discesa
- 🟡 **HOLD** → mercato incerto

Indicatori:
- MA20/MA50 = trend
- RSI = ipercomprato/ipervenduto
- MACD = momentum

⚠️ Non è consulenza finanziaria
""")
