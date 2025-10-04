import asyncio
import httpx
import os
from fastapi import FastAPI
from datetime import datetime, timezone, timedelta
import subprocess

app = FastAPI()

SELF_URL = "https://uni-translator.vercel.app"

bot_process = None  # global

async def ping_self():
    ping_url = f"{SELF_URL}/ping"
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(ping_url)
            if response.status_code == 200:
                print(f"✅ Self-PING success at {ping_url}")
            else:
                print(f"⚠️ Self-PING failed {response.status_code}")
    except Exception as e:
        print(f"❌ Self-PING error: {e}")

async def schedule_ping():
    while True:
        print(f"🌐 Ping at {datetime.now()}")
        await ping_self()
        await asyncio.sleep(600)  # ogni 10 minuti

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(schedule_ping())
    start_bot()  # avvia il bot

def start_bot():
    global bot_process
    if bot_process is None:
        print("🚀 Avvio bot Discord...")
        bot_process = subprocess.Popen(["python3", "main.py"])
    else:
        print("🟢 Bot già in esecuzione")

@app.get("/ping")
async def ping():
    return {"message": "Server awake & bot running"}
