import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import ta
import plotly.graph_objects as go
from sklearn.ensemble import RandomForestClassifier

st.set_page_config(page_title="AI Crypto Bot", layout="wide")

st.title("📊 AI Trading Bot")

st.write("🔄 Analisi automatica in corso...")

# =========================
# DATI
# =========================
@st.cache_data
def get_data(symbol):
    if symbol == "BTC":
        df = yf.download("BTC-USD", period="3mo", interval="1h")
    else:
        df = yf.download("ETH-USD", period="3mo", interval="1h")

    df = df.reset_index()
    df.rename(columns={
        "Datetime": "time",
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Volume": "volume"
    }, inplace=True)

    return df

# =========================
# ANALISI
# =========================
def analyze(df):
    df["rsi"] = ta.momentum.RSIIndicator(df["close"]).rsi()
    df["ma"] = df["close"].rolling(20).mean()
    df = df.dropna()

    df["target"] = np.where(df["close"].shift(-1) > df["close"], 1, 0)

    X = df[["rsi", "ma"]]
    y = df["target"]

    model = RandomForestClassifier(n_estimators=100)
    model.fit(X, y)

    df["prob"] = model.predict_proba(X)[:, 1]

    return df

# =========================
# SEGNALE
# =========================
def signal(df):
    last = df.iloc[-1]

    if last["prob"] > 0.6 and last["close"] > last["ma"]:
        return "BUY"
    elif last["prob"] < 0.4 and last["close"] < last["ma"]:
        return "SELL"
    else:
        return "HOLD"

# =========================
# GRAFICO
# =========================
def plot(df, name):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["time"], y=df["close"], name=name))
    return fig

# =========================
# RUN
# =========================
try:
    btc = analyze(get_data("BTC"))
    eth = analyze(get_data("ETH"))

    st.subheader("📊 Segnali")

    st.write("BTC:", signal(btc))
    st.write("ETH:", signal(eth))

    st.plotly_chart(plot(btc, "BTC"))
    st.plotly_chart(plot(eth, "ETH"))

except Exception as e:
    st.error(f"Errore: {e}")
