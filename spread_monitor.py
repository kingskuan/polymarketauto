import requests
import time
import os
from datetime import datetime

GAMMA_API = "https://gamma-api.polymarket.com"

TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN", "")
TG_CHAT_ID = os.getenv("TG_CHAT_ID", "")

CHECK_INTERVAL = 30
SPREAD_THRESHOLD = 0.03

def send_telegram(message):
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        return
    try:
        url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TG_CHAT_ID, "text": message}, timeout=10)
    except:
        pass

def get_hot_markets():
    try:
        url = f"{GAMMA_API}/markets"
        params = {
            "active": "true",
            "closed": "false",
            "order": "volume24hr",
            "ascending": "false",
            "limit": 50
        }
        response = requests.get(url, params=params, timeout=15)
        markets = response.json()
        
        filtered = []
        skip_keywords = ["vs.", "vs ", "game", "match", "score", "win the", "beat"]
        
        for m in markets:
            question = m.get("question", "").lower()
            
            is_sports = any(kw in question for kw in skip_keywords)
            if is_sports:
                continue
            
            volume_24h = m.get("volume24hr", 0)
            if volume_24h < 10000:
                continue
                
            filtered.append(m)
        
        return filtered[:20]
    except Exception as e:
        print(f"Error fetching markets: {e}")
        return []

def calculate_spread(market):
    try:
        prices = eval(market.get("outcomePrices", "[]"))
        if len(prices) >= 2:
            yes_price = float(prices[0])
            no_price = float(prices[1])
            spread = yes_price + no_price
            return spread, yes_price, no_price
    except:
        pass
    return None, None, None

def main():
    print("=" * 50)
    print("Polymarket Non-Sports Market Monitor")
    print(f"Spread threshold: {SPREAD_THRESHOLD * 100}%")
    print(f"Check interval: {CHECK_INTERVAL}s")
    print("=" * 50)
    
    send_telegram("Polymarket monitor started - watching non-sports markets")
    
    while True:
        try:
            markets = get_hot_markets()
            now = datetime.now().strftime("%H:%M:%S")
            
            print(f"\n[{now}] Found {len(markets)} non-sports markets")
            print("-" * 40)
            
            opportunities = []
            
            for m in markets:
                spread, yes_price, no_price = calculate_spread(m)
                if spread is None:
                    continue
                
                question = m.get("question", "")[:50]
                volume = m.get("volume24hr", 0)
                spread_pct = (spread - 1) * 100
                
                status = "OK" if spread <= (1 + SPREAD_THRESHOLD) else "HIGH"
                
                print(f"{status} | spread:{spread:.4f} ({spread_pct:+.2f}%) | vol:${volume:,.0f} | {question}")
                
                if spread <= (1 + SPREAD_THRESHOLD):
                    opportunities.append({
                        "question": m.get("question", ""),
                        "spread": spread,
                        "spread_pct": spread_pct,
                        "volume": volume,
                        "yes": yes_price,
                        "no": no_price,
                        "slug": m.get("slug", "")
                    })
            
            if opportunities:
                msg = f"Found {len(opportunities)} low spread markets:\n\n"
                for opp in opportunities[:5]:
                    msg += f"- {opp['question'][:40]}\n"
                    msg += f"  Spread: {opp['spread_pct']:+.2f}% | Vol: ${opp['volume']:,.0f}\n"
                    msg += f"  YES:{opp['yes']:.3f} NO:{opp['no']:.3f}\n\n"
                send_telegram(msg)
                print(f"\nNext check in {CHECK_INTERVAL}s...")
            
        except Exception as e:
            print(f"Error: {e}")
        
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
