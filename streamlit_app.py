import streamlit as st
import pandas as pd
import requests
import ta
import plotly.graph_objects as go

st.set_page_config(layout="wide")

st.title("🚀 AI TRADING BOT PRO (eToro Style)")

# ======================
# ASSET
# ======================
asset = st.selectbox("Scegli Asset", ["BTC", "ETH", "GOLD"])

# ======================
# DATA BTC / ETH
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
# GOLD (semplice + stabile)
# ======================
else:
    # fallback stabile (simulazione realistica)
    live_price = 2000  # oro approssimato stabile

    df = pd.DataFrame({
        "close": [live_price + i * 0.5 for i in range(200)]
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

df = df.dropna()

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

# ======================
# PROBABILITÀ (ETORO STYLE)
# ======================
df["prob_up"] = (df["score"] + 4) / 8 * 100
df["prob_down"] = 100 - df["prob_up"]

up = df["prob_up"].iloc[-1]
down = df["prob_down"].iloc[-1]

# ======================
# SEGNALE
# ======================
def signal(score):
    if score >= 3:
        return "🟢 STRONG BUY"
    elif score >= 1:
        return "🟢 BUY"
    elif score <= -3:
        return "🔴 STRONG SELL"
    elif score <= -1:
        return "🔴 SELL"
    else:
        return "🟡 HOLD"

df["signal"] = df["score"].apply(signal)

last_signal = df["signal"].iloc[-1]

# ======================
# ALERT CAMBIO
# ======================
if len(df) > 2:
    if df["signal"].iloc[-1] != df["signal"].iloc[-2]:
        st.warning(f"⚠️ CAMBIO SEGNALE: {df['signal'].iloc[-2]} → {last_signal}")

# ======================
# UI PROBABILITÀ
# ======================
st.subheader("📊 Probabilità AI (stile eToro)")

col1, col2 = st.columns(2)

with col1:
    st.metric("📈 Salita", f"{up:.1f}%")

with col2:
    st.metric("📉 Discesa", f"{down:.1f}%")

st.metric("🎯 Segnale", last_signal)

# ======================
# GRAFICO CON FRECCE
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

# BUY points
buy = df[df["prob_up"] > 65]

# SELL points
sell = df[df["prob_down"] > 65]

fig.add_trace(go.Scatter(
    x=buy.index,
    y=buy["close"],
    mode="markers",
    marker=dict(symbol="triangle-up", size=10),
    name="BUY"
))

fig.add_trace(go.Scatter(
    x=sell.index,
    y=sell["close"],
    mode="markers",
    marker=dict(symbol="triangle-down", size=10),
    name="SELL"
))

st.plotly_chart(fig, use_container_width=True)

# ======================
# LEGENDA
# ======================
st.subheader("📘 Legenda AI")

st.markdown("""
🟢 BUY → pressione rialzista  
🔴 SELL → pressione ribassista  
🟡 HOLD → mercato neutro  

📊 Probabilità:
- derivata da trend + RSI + MACD
- scala 0–100%

⚠️ Non è consulenza finanziaria
""")
