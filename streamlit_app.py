import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Crypto App", layout="wide")

st.title("📊 Crypto Dashboard")

st.write("✅ App funzionante")

# =========================
# DATI SICURI
# =========================
@st.cache_data
def get_data(ticker):
    df = yf.download(ticker, period="1mo", interval="1h")

    if df.empty:
        return None

    return df

# =========================
# BTC
# =========================
btc = get_data("BTC-USD")

if btc is not None:
    st.subheader("Bitcoin")
    st.line_chart(btc["Close"])
else:
    st.error("Errore dati BTC")

# =========================
# ETH
# =========================
eth = get_data("ETH-USD")

if eth is not None:
    st.subheader("Ethereum")
    st.line_chart(eth["Close"])
else:
    st.error("Errore dati ETH")
