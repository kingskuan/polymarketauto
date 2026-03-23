import requests
import time
import csv
import os
from datetime import datetime

API_BASE = "https://clob.polymarket.com"
GAMMA_API = "https://gamma-api.polymarket.com"

TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN", "")
TG_CHAT_ID = os.getenv("TG_CHAT_ID", "")

CHECK_INTERVAL = 1
SPREAD_THRESHOLD = 1.01
LOG_FILE = "spread_log.csv"

def get_active_btc_market():
    try:
        url = f"{GAMMA_API}/markets"
        params = {"closed": "false", "limit": 100}
        response = requests.get(url, params=params, timeout=10)
        markets = response.json()
        for market in markets:
            title = market.get("question", "").lower()
            if "btc" in title and ("5 min" in title or "5-min" in title or "five min" in title):
                return {
                    "id": market.get("conditionId"),
                    "token_id": market.get("clobTokenIds", [""])[0],
                    "question": market.get("question"),
                    "end_time": market.get("endDate")
                }
        for market in markets:
            title = market.get("question", "").lower()
            if "btc" in title and ("minute" in title or "min" in title):
                return {
                    "id": market.get("conditionId"),
                    "token_id": market.get("clobTokenIds", [""])[0],
                    "question": market.get("question"),
                    "end_time": market.get("endDate")
                }
        return None
    except Exception as e:
        print(f"获取市场失败: {e}")
        return None

def get_prices(token_id):
    try:
        url = f"{API_BASE}/book"
        params = {"token_id": token_id}
        response = requests.get(url, params=params, timeout=5)
        data = response.json()
        bids = data.get("bids", [])
        asks = data.get("asks", [])
        if bids and asks:
            best_bid = float(bids[0]["price"])
            best_ask = float(asks[0]["price"])
            spread_total = best_bid + (1 - best_ask)
            return best_bid, 1 - best_ask, spread_total
        return None, None, None
    except Exception as e:
        print(f"获取价格失败: {e}")
        return None, None, None

def send_telegram(message):
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        return
    try:
        url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": TG_CHAT_ID, "text": message}
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Telegram 发送失败: {e}")

def log_to_csv(data):
    file_exists = os.path.exists(LOG_FILE)
    with open(LOG_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["时间", "市场", "YES价格", "NO价格", "总和", "低spread"])
        writer.writerow(data)

def main():
    print("=" * 50)
    print("Polymarket 5分钟 BTC 低 Spread 监控")
    print(f"阈值: <= {SPREAD_THRESHOLD}")
    print(f"Telegram: {'已启用' if TG_BOT_TOKEN else '未启用'}")
    print("=" * 50)
    low_spread_count = 0
    total_checks = 0
    current_market = None
    send_telegram("Polymarket 5分钟 BTC 监控已启动")
    while True:
        try:
            if current_market is None:
                print(f"[{datetime.now()}] 搜索活跃的 5 分钟 BTC 市场...")
                current_market = get_active_btc_market()
                if current_market:
                    print(f"找到市场: {current_market['question']}")
                    send_telegram(f"新市场: {current_market['question']}")
                else:
                    print("未找到活跃市场，30 秒后重试...")
                    time.sleep(30)
                    continue
            yes_price, no_price, total = get_prices(current_market["token_id"])
            if yes_price is None:
                print("价格获取失败，可能市场已结束，切换新市场...")
                current_market = None
                time.sleep(5)
                continue
            total_checks += 1
            now = datetime.now()
            time_str = now.strftime("%Y-%m-%d %H:%M:%S")
            is_low_spread = total <= SPREAD_THRESHOLD
            if is_low_spread:
                low_spread_count += 1
                print(f"[低SPREAD] {time_str}")
                print(f"   YES: {yes_price:.4f} | NO: {no_price:.4f} | 总和: {total:.4f}")
                log_to_csv([time_str, current_market["question"][:30], yes_price, no_price, total, "是"])
                send_telegram(f"低Spread!\nYES: {yes_price:.4f}\nNO: {no_price:.4f}\n总和: {total:.4f}\n累计: {low_spread_count}/{total_checks}")
            else:
                log_to_csv([time_str, current_market["question"][:30], yes_price, no_price, total, "否"])
                if total_checks % 60 == 0:
                    rate = low_spread_count / total_checks * 100 if total_checks > 0 else 0
                    print(f"[{time_str}] YES: {yes_price:.4f} | NO: {no_price:.4f} | 总和: {total:.4f} | 低spread: {rate:.1f}%")
            if total_checks % 3600 == 0:
                rate = low_spread_count / total_checks * 100
                send_telegram(f"每小时报告\n检查: {total_checks}\n低spread: {low_spread_count} ({rate:.1f}%)")
            time.sleep(CHECK_INTERVAL)
        except KeyboardInterrupt:
            print("\n停止监控")
            break
        except Exception as e:
            print(f"错误: {e}")
            current_market = None
            time.sleep(10)

if __name__ == "__main__":
    main()
