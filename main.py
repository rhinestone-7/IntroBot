import discord
import json
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("TOKEN")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "channels.json")

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

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

    # COMMAND: set intro channel
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

    # COMMAND: remove intro channel
    if message.content.startswith("!removeintro"):
        if guild_id in intro_channels:
            if message.channel.id in intro_channels[guild_id]:
                intro_channels[guild_id].remove(message.channel.id)
                save_data(intro_channels)
                await message.channel.send("❌ Channel removed from intro list")
            else:
                await message.channel.send("⚠️ This channel is not in intro list")
        return

    # COMMAND: clear all intro channels
    if message.content.startswith("!clearintro"):
        intro_channels[guild_id] = []
        save_data(intro_channels)
        await message.channel.send("🧹 All intro channels cleared")
        return

    # Get channel list
    channels = intro_channels.get(guild_id, [])

    # Only process if message is in an allowed channel
    if message.channel.id not in channels:
        return

    # Delete the original message first
    try:
        await message.delete()
    except discord.Forbidden:
        print("Missing Manage Messages permission")

    # Get or create webhook
    try:
        webhooks = await message.channel.webhooks()
        webhook = discord.utils.get(webhooks, name="IntroHook")
        if webhook is None:
            webhook = await message.channel.create_webhook(name="IntroHook")
    except discord.Forbidden:
        print("Missing Manage Webhooks permission")
        return

    # Build embed
    embed = discord.Embed(
        title="📌 Introduction",
        description=message.content,
        color=discord.Color.brand_red()
    )
    embed.set_thumbnail(url=message.author.display_avatar.url)

    # Send as the member
    await webhook.send(
        content=f"**Hi everyone, I'm {message.author.mention} 👋**",
        embed=embed,
        username=message.author.display_name,
        avatar_url=message.author.display_avatar.url,
        allowed_mentions=discord.AllowedMentions(users=False)
    )

client.run(TOKEN)