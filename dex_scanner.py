import requests
import time
import os
import threading
from datetime import datetime

TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_IDS = [int(x) for x in os.environ.get("CHAT_IDS", "").split(",") if x.strip()]

# ←←← WPISZ TU SWÓJ PRYWATNY CHAT_ID (ten, na którym teraz czytasz)
MY_PRIVATE_ID = 542711955          # <—— ZMIEŃ JEŚLI MASZ INNY

seen = set()

# ============== WYSYŁANIE WIADOMOŚCI ==============
def send(msg, to_private=False):
    """
    to_private=True  → tylko do Ciebie (błędy, debug)
    to_private=False → do wszystkich (grupa + Ty)
    """
    for cid in CHAT_IDS:
        try:
            if to_private and cid != MY_PRIVATE_ID:
                continue
            requests.post(
                f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                data={"chat_id": cid, "text": msg, "parse_mode": "HTML",
                      "disable_web_page_preview": True},
                timeout=10
            )
        except:
            pass

# ============== START & HEARTBEAT ==============
def heartbeat():
    send(f"DEX Scanner żyje – {datetime.now().strftime('%H:%M')}")

send("DEX Pump Scanner 2025 uruchomiony\nSolana • Base • Ethereum • BSC\nCzekam na 50–1000x")
heartbeat()

# ============== KOMENDY (działają tylko od Ciebie) ==============
def polling():
    offset = 0
    while True:
        try:
            r = requests.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates",
                             params={"offset": offset, "timeout": 10}, timeout=10).json()
            for u in r.get("result", []):
                if "message" in u:
                    cid = u["message"]["chat"]["id"]
                    txt = u["message"].get("text", "").lower().strip()
                    if cid == MY_PRIVATE_ID:  # tylko Ty możesz używać komend
                        if txt in ["/start", "/help"]:
                            send("DEX Pump Scanner 2025\n\nKomendy (tylko Ty):\n/status – czy żyję\n/top – ostatnie pompy")
                        elif txt == "/status":
                            send("Żyję i skanuję 4 chainy non-stop")
                    offset = u["update_id"] + 1
        except:
            pass
        time.sleep(7)

threading.Thread(target=polling, daemon=True).start()

print("DEX Scanner 2025 działa 24/7!")

# ============== GŁÓWNA PĘTLA SKANOWANIA ==============
while True:
    try:
        # Solana – najszybsze i najmocniejsze
        try:
            r = requests.get("https://api.dexscreener.com/latest/dex/tokens?chain=solana&orderBy=volume5m&order=desc&limit=80", timeout=12).json()
            for p in r.get("pairs", []):
                try:
                    pair = p["pairAddress"]
                    if pair in seen: continue
                    base = p["baseToken"]["symbol"]
                    liq = p.get("liquidity", {}).get("usd", 0) or 0
                    vol5m = p.get("volume", {}).get("m5", 0) or 0
                    change5m = p.get("priceChange", {}).get("m5", 0) or 0
                    age_min = (time.time() - p.get("pairCreatedAt", 0)/1000) / 60

                    if liq >= 25_000 and vol5m >= 70_000 and change5m >= 20 and age_min <= 300:
                        msg = f"NOWA POMPA {base}\n" \
                              f"Solana • +{change5m}% (5 min)\n" \
                              f"Vol 5m: ${vol5m:,.0f} • Liq: ${liq:,.0f}\n" \
                              f"https://dexscreener.com/solana/{pair}"
                        send(msg)               # ← czysty alert → do wszystkich
                        seen.add(pair)
                except: continue
        except Exception as e:
            send(f"DEX błąd (Solana): {e}", to_private=True)   # ← tylko Ty widzisz

        # Base + ETH + BSC
        for chain in ["base", "ethereum", "bsc"]:
            try:
                r = requests.get(f"https://api.dexscreener.com/latest/dex/pairs/{chain}?limit=60", timeout=10).json()
                for p in r.get("pairs", []):
                    pair = p["pairAddress"]
                    if pair in seen: continue
                    base = p["baseToken"]["symbol"]
                    liq = p.get("liquidity", {}).get("usd", 0) or 0
                    vol5m = p.get("volume", {}).get("m5", 0) or 0
                    change5m = p.get("priceChange", {}).get("m5", 0) or 0

                    if liq >= 30_000 and vol5m >= 80_000 and change5m >= 22:
                        msg = f"NOWA POMPA {base}\n" \
                              f"{chain.upper()} • +{change5m}%\n" \
                              f"Vol 5m: ${vol5m:,.0f} • Liq: ${liq:,.0f}\n" \
                              f"https://dexscreener.com/{chain}/{pair}"
                        send(msg)
                        seen.add(pair)
            except Exception as e:
                send(f"DEX błąd ({chain}): {e}", to_private=True)
            time.sleep(1)

        # heartbeat co 30 min
        if int(time.time()) % 1800 < 60:
            heartbeat()

        time.sleep(60)

    except Exception as e:
        send(f"DEX krytyczny błąd: {e}", to_private=True)
        time.sleep(60)
