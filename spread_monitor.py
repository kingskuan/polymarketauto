python
import requests
import time
import os
from datetime import datetime

TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN", "")
TG_CHAT_ID = os.getenv("TG_CHAT_ID", "")

def send_telegram(message):
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        print("Telegram 未配置")
        return
    try:
        url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": TG_CHAT_ID, "text": message}
        requests.post(url, json=payload, timeout=5)
        print("Telegram 已发送")
    except Exception as e:
        print(f"Telegram 失败: {e}")

def main():
    print("监控启动中...")
    print(f"TG_BOT_TOKEN: {'已设置' if TG_BOT_TOKEN else '未设置'}")
    print(f"TG_CHAT_ID: {'已设置' if TG_CHAT_ID else '未设置'}")
    send_telegram("测试消息 - Polymarket 监控已启动")
    count = 0
    while True:
        count += 1
        print(f"[{datetime.now()}] 运行中... 第 {count} 次")
        time.sleep(60)

if __name__ == "__main__":
    main()
