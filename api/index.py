import asyncio
import httpx
from fastapi import FastAPI
from datetime import datetime, timezone, timedelta

app = FastAPI()

SELF_URL = "https://NOME-PROGETTO.vercel.app"  # <-- la metti dopo il deploy su Vercel

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

@app.get("/ping")
async def ping():
    return {"message": "Server awake!"}
