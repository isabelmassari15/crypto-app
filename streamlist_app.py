import streamlit as st
import pandas as pd
import numpy as np
import ccxt
import ta
import plotly.graph_objects as go

st.set_page_config(page_title="Crypto AI App", layout="wide")

st.title("📊 Crypto AI Signals (BTC & ETH)")

exchange = ccxt.binance()

def get_data(symbol):
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe='1h', limit=200)
    df = pd.DataFrame(ohlcv, columns=['time','open','high','low','close','volume'])
    df['time'] = pd.to_datetime(df['time'], unit='ms')
    return df

def analyze(df):
    df['rsi'] = ta.momentum.RSIIndicator(df['close']).rsi()
    df['ma'] = df['close'].rolling(20).mean()

    signals = []

    for i in range(len(df)):
        if df['rsi'][i] < 30 and df['close'][i] > df['ma'][i]:
            signals.append("BUY")
        elif df['rsi'][i] > 70 and df['close'][i] < df['ma'][i]:
            signals.append("SELL")
        else:
            signals.append("HOLD")

    df['signal'] = signals
    return df

def plot_chart(df, name):
    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=df['time'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name=name
    ))

    buys = df[df['signal'] == "BUY"]
    sells = df[df['signal'] == "SELL"]

    fig.add_trace(go.Scatter(
        x=buys['time'],
        y=buys['close'],
        mode='markers',
        marker=dict(symbol='arrow-up', size=12),
        name='BUY'
    ))

    fig.add_trace(go.Scatter(
        x=sells['time'],
        y=sells['close'],
        mode='markers',
        marker=dict(symbol='arrow-down', size=12),
        name='SELL'
    ))

    return fig

st.subheader("Bitcoin (BTC/USDT)")
btc = analyze(get_data("BTC/USDT"))
st.plotly_chart(plot_chart(btc, "BTC"))

st.subheader("Ethereum (ETH/USDT)")
eth = analyze(get_data("ETH/USDT"))
st.plotly_chart(plot_chart(eth, "ETH"))

st.success("Sistema AI attivo (RSI + Media Mobile)") 
