import requests
import time
import os
import threading
from datetime import datetime

TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = int(os.environ.get("CHAT_ID"))

seen = set()

def send(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                      data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML", "disable_web_page_preview": True}, timeout=10)
    except: pass

def heartbeat():
    send(f"DEX Scanner żyje – {datetime.now().strftime('%H:%M')}")

send("DEX Pump Scanner 2025 uruchomiony\nSolana • Base • Ethereum • BSC\nCzekam na 50–1000x")
heartbeat()

def polling():
    offset = 0
    while True:
        try:
            r = requests.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates", params={"offset": offset, "timeout": 10}).json()
            for u in r.get("result", []):
                if "message" in u and u["message"]["chat"]["id"] == CHAT_ID:
                    txt = u["message"].get("text","").lower()
                    if txt in ["/start","/help"]:
                        send("DEX Pump Scanner 2025\n\nKomendy:\n/status – czy żyję\n/top – ostatnie pompy")
                    elif txt == "/status":
                        send("Żyję i skanuję 4 chainy 24/7")
                    offset = u["update_id"] + 1
        except: pass
        time.sleep(7)

threading.Thread(target=polling, daemon=True).start()

print("DEX Scanner 2025 działa!")

while True:
    try:
        # Solana – najszybsze API
        r = requests.get("https://api.dexscreener.com/latest/dex/tokens?chain=solana&orderBy=volume5m&order=desc&limit=80", timeout=12).json()
        for p in r.get("pairs", []):
            try:
                base = p["baseToken"]["symbol"]
                pair = p["pairAddress"]
                if pair in seen: continue

                liq = p.get("liquidity", {}).get("usd", 0) or 0
                vol5m = p.get("volume", {}).get("m5", 0) or 0
                change5m = p.get("priceChange", {}).get("m5", 0) or 0
                age = (time.time() - p.get("pairCreatedAt", 0)/1000) / 60  # minuty

                if (liq >= 25_000 and vol5m >= 70_000 and change5m >= 20 and age <= 300):
                    msg = f"NOWA POMPA {base}\n" \
                          f"Solana • +{change5m}% (5 min)\n" \
                          f"Vol 5m: ${vol5m:,.0f} • Liq: ${liq:,.0f}\n" \
                          f"https://dexscreener.com/solana/{pair}"
                    send(msg)
                    seen.add(pair)
            except: continue

        # Base + ETH + BSC (krótsze zapytania co 15–20 sekund
        for chain in ["base", "ethereum", "bsc"]:
            try:
                r = requests.get(f"https://api.dexscreener.com/latest/dex/pairs/{chain}?limit=50", timeout=8).json()
                for p in r.get("pairs", []):
                    pair = p["pairAddress"]
                    if pair in seen: continue
                    base = p["baseToken"]["symbol"]
                    liq = p.get("liquidity", {}).get("usd", 0) or 0
                    vol5m = p.get("volume", {}).get("m5", 0) or 0
                    change5m = p.get("priceChange", {}).get("m5", 0) or 0
                    if liq >= 30_000 and vol5m >= 80_000 and change5m >= 22:
                        msg = f"NOWA POMPA {base}\n{chain.upper()} • +{change5m}%\nhttps://dexscreener.com/{chain}/{pair}"
                        send(msg)
                        seen.add(pair)
            except: continue
            time.sleep(2)

        if int(time.time()) % 1800 < 60:
            heartbeat()

        time.sleep(60)

    except Exception as e:
        send(f"DEX błąd: {e}")
        time.sleep(60)
