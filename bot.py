import time
import requests
import hmac
import hashlib
import os
from datetime import datetime

API_KEY = os.getenv('API_KEY')
API_SECRET = os.getenv('API_SECRET')
BASE_URL = 'https://api.binance.com'

# --- Strategy settings ---
SYMBOLS = ['BTCUSDT', 'ETHUSDT']
RSI_PERIOD = 14
EMA_PERIOD = 9
INTERVAL = '15m'

def get_klines(symbol, interval, limit=100):
    url = f"{BASE_URL}/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    response = requests.get(url)
    return [float(k[4]) for k in response.json()]  # closing prices

def calculate_rsi(prices):
    gains = []
    losses = []
    for i in range(1, len(prices)):
        delta = prices[i] - prices[i - 1]
        if delta >= 0:
            gains.append(delta)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(-delta)
    avg_gain = sum(gains[-RSI_PERIOD:]) / RSI_PERIOD
    avg_loss = sum(losses[-RSI_PERIOD:]) / RSI_PERIOD
    rs = avg_gain / avg_loss if avg_loss > 0 else 0
    return 100 - (100 / (1 + rs))

def calculate_ema(prices, period):
    k = 2 / (period + 1)
    ema = prices[0]
    for price in prices[1:]:
        ema = (price * k) + (ema * (1 - k))
    return ema

def sign_request(params):
    query_string = '&'.join([f"{key}={params[key]}" for key in sorted(params)])
    signature = hmac.new(API_SECRET.encode(), query_string.encode(), hashlib.sha256).hexdigest()
    return f"{query_string}&signature={signature}"

def place_order(symbol, side, quantity):
    url = f"{BASE_URL}/api/v3/order"
    params = {
        'symbol': symbol,
        'side': side,
        'type': 'MARKET',
        'quantity': quantity,
        'timestamp': int(time.time() * 1000)
    }
    headers = {'X-MBX-APIKEY': API_KEY}
    signed_params = sign_request(params)
    response = requests.post(f"{url}?{signed_params}", headers=headers)
    print(f"{side} order placed: {response.json()}")

def run_bot():
    while True:
        for symbol in SYMBOLS:
            try:
                prices = get_klines(symbol, INTERVAL)
                rsi = calculate_rsi(prices)
                ema = calculate_ema(prices, EMA_PERIOD)
                current_price = prices[-1]

                print(f"[{datetime.now()}] {symbol}: Price={current_price}, RSI={rsi:.2f}, EMA={ema:.2f}")

                balance = 0.001  # fixed quantity for testing

                if rsi < 30 and current_price > ema:
                    print(f"BUY signal for {symbol}")
                    place_order(symbol, 'BUY', balance)

                elif rsi > 70 and current_price < ema:
                    print(f"SELL signal for {symbol}")
                    place_order(symbol, 'SELL', balance)

            except Exception as e:
                print(f"Error for {symbol}: {e}")
        time.sleep(60 * 15)  # run every 15 minutes

if __name__ == '__main__':
    run_bot()
