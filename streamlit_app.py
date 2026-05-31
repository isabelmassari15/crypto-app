import streamlit as st
import pandas as pd
import requests
import ta
import plotly.graph_objects as go

st.set_page_config(layout="wide")

st.title("🚀 AI TRADING BOT PRO (BTC + ETH + GOLD)")

# ======================
# ASSET
# ======================
asset = st.selectbox("Scegli Asset", ["BTC", "ETH", "GOLD"])

# ======================
# BTC / ETH DATA
# ======================
if asset in ["BTC", "ETH"]:

    coin_map = {
        "BTC": "bitcoin",
        "ETH": "ethereum"
    }

    coin_id = coin_map[asset]

    # prezzo live
    price_url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
    live_price = requests.get(price_url).json()[coin_id]["usd"]

    # storico
    chart_url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days=7"
    data = requests.get(chart_url).json()

    df = pd.DataFrame(data["prices"], columns=["time", "close"])
    df["time"] = pd.to_datetime(df["time"], unit="ms")

# ======================
# GOLD DATA
# ======================
else:
    url = "https://api.metals.live/v1/spot/gold"
    r = requests.get(url).json()

    live_price = float(r[0]["price"])

    # simulazione storica (per avere grafico)
    df = pd.DataFrame({
        "close": [live_price * (1 + i/2000) for i in range(200)]
    })

# ======================
# PREZZO LIVE
# ======================
st.metric("💰 Prezzo LIVE", f"{live_price:.2f} $")

# ======================
# INDICATORI
# ======================
df["ma20"] = df["close"].rolling(20).mean()
df["ma50"] = df["close"].rolling(50).mean()

df["rsi"] = ta.momentum.RSIIndicator(df["close"]).rsi()

macd = ta.trend.MACD(df["close"])
df["macd"] = macd.macd()
df["macd_signal"] = macd.macd_signal()

df["volatility"] = df["close"].rolling(10).std()

# ======================
# AI SCORE
# ======================
df["score"] = 0

df.loc[df["ma20"] > df["ma50"], "score"] += 2
df.loc[df["ma20"] < df["ma50"], "score"] -= 2

df.loc[df["rsi"] < 30, "score"] += 2
df.loc[df["rsi"] > 70, "score"] -= 2

df.loc[df["macd"] > df["macd_signal"], "score"] += 1
df.loc[df["macd"] < df["macd_signal"], "score"] -= 1

df.loc[df["volatility"] > df["volatility"].mean(), "score"] -= 1

# ======================
# SIGNAL
# ======================
def get_signal(score):
    if score >= 4:
        return "🟢 STRONG BUY"
    elif score >= 2:
        return "🟢 BUY"
    elif score <= -4:
        return "🔴 STRONG SELL"
    elif score <= -2:
        return "🔴 SELL"
    else:
        return "🟡 HOLD"

df["signal"] = df["score"].apply(get_signal)

last_signal = df["signal"].iloc[-1]
last_score = df["score"].iloc[-1]

# ======================
# ALERT CAMBIO SEGNALE
# ======================
if len(df) > 2:
    prev_signal = df["signal"].iloc[-2]
    if prev_signal != last_signal:
        st.warning(f"⚠️ CAMBIO SEGNALE: {prev_signal} → {last_signal}")

# ======================
# DASHBOARD
# ======================
st.subheader("📊 ANALISI AI")

col1, col2 = st.columns(2)

with col1:
    st.metric("Segnale", last_signal)

with col2:
    st.metric("Score", int(last_score))

# ======================
# GRAFICO
# ======================
fig = go.Figure()

fig.add_trace(go.Scatter(
    y=df["close"],
    name="Price"
))

fig.add_trace(go.Scatter(
    y=df["ma20"],
    name="MA20"
))

fig.add_trace(go.Scatter(
    y=df["ma50"],
    name="MA50"
))

st.plotly_chart(fig, use_container_width=True)

# ======================
# LEGENDA
# ======================
st.subheader("📘 Legenda")

st.markdown("""
🟢 BUY → trend positivo + momentum  
🔴 SELL → pressione ribassista  
🟡 HOLD → mercato incerto  

Indicatori:
- MA20 / MA50 → trend
- RSI → ipercomprato/ipervenduto
- MACD → momentum
- Volatilità → rischio

⚠️ Non è consulenza finanziaria
""")
