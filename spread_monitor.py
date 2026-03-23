import requests
import time
import os
from datetime import datetime

API_BASE = "https://clob.polymarket.com"

TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN", "")
TG_CHAT_ID = os.getenv("TG_CHAT_ID", "")

CHECK_INTERVAL = 1
SPREAD_THRESHOLD = 1.01

def send_telegram(message):
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        return
    try:
        url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TG_CHAT_ID, "text": message}, timeout=5)
    except:
        pass

def get_current_5min_market():
    try:
        url = "https://polymarket.com/api/events/btc-updown-5m"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            markets = data.get("markets", [])
            for m in markets:
                if not m.get("closed", True):
                    tokens = m.get("clobTokenIds", [])
                    if tokens:
                        return {
                            "question": m.get("question", ""),
                            "token_yes": tokens[0] if len(tokens) > 0 else None,
                            "token_no": tokens[1] if len(tokens) > 1 else None
                        }
        return None
    except Exception as e:
        print(f"Error getting market: {e}")
        return None

def get_orderbook(token_id):
    try:
        url = f"{API_BASE}/book"
        params = {"token_id": token_id}
        response = requests.get(url, params=params, timeout=5)
        data = response.json()
        bids = data.get("bids", [])
        asks = data.get("asks", [])
        if bids and asks:
            return float(bids[0]["price"]), float(asks[0]["price"])
        return None, None
    except:
        return None, None

def main():
    print("=" * 50)
    print("Polymarket 5-min BTC Spread Monitor")
    print(f"Threshold: <= {SPREAD_THRESHOLD}")
    print(f"Telegram: {'Enabled' if TG_BOT_TOKEN else 'Disabled'}")
    print("=" * 50)
    
    send_telegram("5-min BTC Monitor Started")
    
    check_count = 0
    low_spread_count = 0
    
    while True:
        try:
            market = get_current_5min_market()
            
            if not market:
                print(f"[{datetime.now()}] No active 5-min market, retry in 10s...")
                time.sleep(10)
                continue
            
            yes_bid, yes_ask = get_orderbook(market["token_yes"])
            
            if yes_bid is None:
                time.sleep(2)
                continue
            
            spread = yes_ask - yes_bid
            total = yes_bid + (1 - yes_ask)
            
            check_count += 1
            
            if total <= SPREAD_THRESHOLD:
                low_spread_count += 1
                msg = f"LOW SPREAD!\n{market['question'][:40]}\nYES: {yes_bid:.3f}/{yes_ask:.3f}\nSpread: {spread:.4f}\nTotal: {total:.4f}"
                print(f"[{datetime.now()}] {msg}")
                send_telegram(msg)
            
            if check_count % 60 == 0:
                print(f"[{datetime.now()}] Checks: {check_count} | Low spreads: {low_spread_count}")
            
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
