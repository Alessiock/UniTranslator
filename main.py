import os
import asyncio
from typing import Optional, Dict

from dotenv import load_dotenv
import discord
from discord import app_commands
from googletrans import Translator

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
APP_ID = os.getenv("APP_ID")

# Intents base per leggere messaggi e usare slash commands
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

translator = Translator()

# Config in RAM (gratis, zero db). Si resetta a ogni riavvio.
# channel_id -> {"in": "auto", "out": "en", "auto": False}
per_channel: Dict[int, Dict[str, object]] = {}

DEFAULT_IN = "auto"
DEFAULT_OUT = "en"

# --- Helpers -----------------------------------------------------------------

def get_cfg(channel_id: int) -> Dict[str, object]:
    cfg = per_channel.get(channel_id)
    if not cfg:
        cfg = {"in": DEFAULT_IN, "out": DEFAULT_OUT, "auto": False}
        per_channel[channel_id] = cfg
    return cfg

async def do_translate(text: str, src: str, dest: str) -> str:
    # googletrans usa endpoint non ufficiali: può fallire/sporadici 429 -> retry soft
    for attempt in range(2):
        try:
            # NB: src="auto" è supportato
            result = translator.translate(text, src=src, dest=dest)
            return result.text
        except Exception as e:
            if attempt == 0:
                await asyncio.sleep(0.8)
            else:
                raise e

# --- Bot lifecycle -----------------------------------------------------------

@client.event
async def on_ready():
    try:
        # sync comandi globali
        await tree.sync()
        print(f"Logged in as {client.user} | Slash commands synced")
    except Exception as e:
        print("Slash sync error:", e)

# --- Slash commands ----------------------------------------------------------

@tree.command(name="translate", description="Traduci un testo (usa googletrans)")
@app_commands.describe(text="Testo da tradurre", to="Lingua target (es. en, it, es, ar...)", src="Lingua sorgente (default auto)")
async def translate_cmd(interaction: discord.Interaction, text: str, to: str, src: Optional[str] = "auto"):
    await interaction.response.defer(thinking=True, ephemeral=False)
    try:
        out = await do_translate(text, src or "auto", to)
        await interaction.followup.send(f"🌍 **{src or 'auto'} → {to}**\n{out[:1900]}")
    except Exception as e:
        await interaction.followup.send("❌ Errore durante la traduzione. Riprova tra poco.")

@tree.command(name="setlang", description="Imposta lingue default per il canale")
@app_commands.describe(inp="Lingua input (es. auto/it/en/...)", out="Lingua output (es. en/it/...)")
async def setlang_cmd(interaction: discord.Interaction, inp: Optional[str] = None, out: Optional[str] = None):
    cfg = get_cfg(interaction.channel_id)
    if inp: cfg["in"] = inp
    if out: cfg["out"] = out
    await interaction.response.send_message(
        f"✅ Lingue canale impostate: in=`{cfg['in']}` → out=`{cfg['out']}`", ephemeral=True
    )

@tree.command(name="autotranslate", description="Abilita/disabilita traduzione automatica del canale")
@app_commands.describe(state="on/off")
async def autotranslate_cmd(interaction: discord.Interaction, state: str):
    cfg = get_cfg(interaction.channel_id)
    cfg["auto"] = state.lower() == "on"
    await interaction.response.send_message(
        f"🔁 Traduzione automatica: **{'ON' if cfg['auto'] else 'OFF'}**", ephemeral=True
    )

# --- Auto-translate dei messaggi --------------------------------------------

@client.event
async def on_message(message: discord.Message):
    if message.author.bot or not message.content:
        return
    cfg = per_channel.get(message.channel.id)
    if not cfg or not cfg.get("auto"):
        return
    # Evita loop: non ritradurre i messaggi del bot
    try:
        translated = await do_translate(message.content, cfg["in"], cfg["out"])
        if translated and translated.strip() and translated.strip() != message.content.strip():
            await message.reply(translated[:1900], mention_author=False)
    except Exception:
        # Silenzioso: se Google blocca temporaneamente, il bot non spamma errori
        pass

if __name__ == "__main__":
    if not TOKEN:
        raise SystemExit("DISCORD_BOT_TOKEN mancante")
    client.run(TOKEN)
