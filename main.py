import discord
import json
from dotenv import load_dotenv
import os
from flask import Flask
from threading import Thread

load_dotenv()
TOKEN = os.getenv("TOKEN")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "channels.json")
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# KeepAlive
app = Flask(__name__)

@app.route('/')
def home():
    return "ok", 200

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

intro_channels = load_data()

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

@client.event
async def on_message(message):
    if message.author.bot:
        return
    guild_id = str(message.guild.id)
    if message.content.startswith("!setintro"):
        if guild_id not in intro_channels:
            intro_channels[guild_id] = []
        if message.channel.id not in intro_channels[guild_id]:
            intro_channels[guild_id].append(message.channel.id)
            save_data(intro_channels)
            await message.channel.send("✅ Intro channel set successfully!")
        else:
            await message.channel.send("⚠️ This channel is already in the intro list!")
        return
    if message.content.startswith("!removeintro"):
        if guild_id in intro_channels:
            if message.channel.id in intro_channels[guild_id]:
                intro_channels[guild_id].remove(message.channel.id)
                save_data(intro_channels)
                await message.channel.send("❌ Channel removed from intro list")
            else:
                await message.channel.send("⚠️ This channel is not in intro list")
        return
    if message.content.startswith("!clearintro"):
        intro_channels[guild_id] = []
        save_data(intro_channels)
        await message.channel.send("🧹 All intro channels cleared")
        return
    channels = intro_channels.get(guild_id, [])
    if message.channel.id not in channels:
        return
    try:
        await message.delete()
    except discord.Forbidden:
        print("Missing Manage Messages permission")
    try:
        webhooks = await message.channel.webhooks()
        webhook = discord.utils.get(webhooks, name="IntroHook")
        if webhook is None:
            webhook = await message.channel.create_webhook(name="IntroHook")
    except discord.Forbidden:
        print("Missing Manage Webhooks permission")
        return
    embed = discord.Embed(
        title="📌 Introduction",
        description=message.content,
        color=discord.Color.brand_red()
    )
    embed.set_thumbnail(url=message.author.display_avatar.url)
    await webhook.send(
        content=f"**Hi everyone, I'm {message.author.mention} 👋**",
        embed=embed,
        username=message.author.display_name,
        avatar_url=message.author.display_avatar.url,
        allowed_mentions=discord.AllowedMentions(users=False)
    )

keep_alive()
client.run(TOKEN)
