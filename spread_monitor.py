import requests
import time
import os
from datetime import datetime

GAMMA_API = "https://gamma-api.polymarket.com"
API_BASE = "https://clob.polymarket.com"

TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN", "")
TG_CHAT_ID = os.getenv("TG_CHAT_ID", "")

SPREAD_THRESHOLD = 1.02

def send_telegram(message):
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        return
    try:
        url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TG_CHAT_ID, "text": message}, timeout=5)
    except:
        pass

def get_all_markets():
    try:
        url = f"{GAMMA_API}/markets"
        params = {"closed": "false", "limit": 50}
        response = requests.get(url, params=params, timeout=10)
        return response.json()
    except Exception as e:
        print(f"API error: {e}")
        return []

def main():
    print("=" * 50)
    print("Polymarket Market Scanner")
    print("=" * 50)
    send_telegram("Polymarket Scanner Started")
    
    markets = get_all_markets()
    print(f"Found {len(markets)} markets")
    
    btc_markets = []
    for m in markets:
        title = m.get("question", "").lower()
        if "btc" in title or "bitcoin" in title:
            btc_markets.append(m)
            print(f"BTC Market: {m.get('question', 'N/A')[:60]}")
    
    print(f"\nTotal BTC markets: {len(btc_markets)}")
    
    if btc_markets:
        send_telegram(f"Found {len(btc_markets)} BTC markets")
        for m in btc_markets[:5]:
            print(f"\n--- Market ---")
            print(f"Question: {m.get('question', 'N/A')}")
            print(f"ID: {m.get('conditionId', 'N/A')}")
            print(f"Tokens: {m.get('clobTokenIds', [])}")
    else:
        send_telegram("No BTC markets found - checking all markets")
        print("\nAll market titles:")
        for m in markets[:20]:
            print(f"- {m.get('question', 'N/A')[:70]}")
    
    print("\nKeeping alive...")
    while True:
        time.sleep(300)
        print(f"[{datetime.now()}] Still running")

if __name__ == "__main__":
    main()
