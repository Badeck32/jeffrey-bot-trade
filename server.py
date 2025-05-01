# ✅ server.py PATCHÉ POUR BITGET (Signature FIX)
from flask import Flask, request, jsonify
import requests
import hmac
import hashlib
import time
import json
import os

app = Flask(__name__)

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
API_PASSPHRASE = os.getenv("API_PASSPHRASE")
BASE_URL = 'https://api.bitget.com'

def generate_signature(timestamp, method, request_path, body=''):
    message = f"{timestamp}{method.upper()}{request_path}{body}"
    signature = hmac.new(
        API_SECRET.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return signature

def get_balance():
    timestamp = str(int(time.time() * 1000))
    path = '/api/mix/v1/account/accounts?productType=umcbl'
    signature = generate_signature(timestamp, 'GET', path)
    headers = {
        'ACCESS-KEY': API_KEY,
        'ACCESS-SIGN': signature,
        'ACCESS-TIMESTAMP': timestamp,
        'ACCESS-PASSPHRASE': API_PASSPHRASE,
    }
    response = requests.get(BASE_URL + path, headers=headers)
    data = response.json()
    if not data.get('data'):
        print(f"Erreur balance: {data}")
        return 0
    for account in data['data']:
        if account['marginCoin'] == 'USDT':
            balance = float(account['available'])
            print(f"Balance USDT trouvée: {balance}")
            return balance
    print("Pas de balance USDT trouvée.")
    return 0

def place_order(side, symbol, risk_pct=0.05, leverage=20):
    balance = get_balance()
    if balance == 0:
        print("Balance nulle, pas d'ordre envoyé.")
        return {"error": "Balance nulle"}

    max_loss = balance * risk_pct
    entry_price = 1
    sl_distance = 0.01 * entry_price
    qty = (max_loss * leverage) / sl_distance
    qty = round(qty, 3)

    timestamp = str(int(time.time() * 1000))
    path = '/api/mix/v1/order/placeOrder'
    body = {
        "symbol": symbol,
        "marginCoin": "USDT",
        "size": str(qty),
        "side": side,
        "orderType": "market",
        "force": True,
        "leverage": leverage,
        "openType": "cross",
    }
    body_json = json.dumps(body)

    signature = generate_signature(timestamp, 'POST', path, body_json)

    headers = {
        'ACCESS-KEY': API_KEY,
        'ACCESS-SIGN': signature,
        'ACCESS-TIMESTAMP': timestamp,
        'ACCESS-PASSPHRASE': API_PASSPHRASE,
        'Content-Type': 'application/json'
    }

    response = requests.post(BASE_URL + path, headers=headers, data=body_json)
    print(f"Réponse Bitget : {response.text}")
    return response.json()

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        if data is None:
            return "Invalid payload", 400

        side = data.get("side")
        symbol = data.get("symbol")

        if not side or not symbol:
            return "Missing side or symbol", 400

        print(f"Webhook reçu : {data}")

        result = place_order(side, symbol)
        return jsonify(result)
    except Exception as e:
        print(f"Erreur Webhook : {e}")
        return "Internal Server Error", 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)

