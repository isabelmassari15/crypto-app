import yfinance as yf

def get_data(symbol):
    if symbol == "BTC/USDT":
        df = yf.download("BTC-USD", period="7d", interval="1h")
    else:
        df = yf.download("ETH-USD", period="7d", interval="1h")

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
