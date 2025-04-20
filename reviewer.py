import discord
from discord.ext import commands
import os
import json
import asyncio
from datetime import datetime, UTC

DATA_FILE = 'reviews.json'

def ensure_data_file():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'w') as f:
            json.dump({}, f, indent=4)

# --- Read secrets.txt for owner id ---
OWNER_ID = None
BOT_TOKEN = None
with open('secrets.txt', 'r') as f:
    lines = f.readlines()
    if len(lines) >= 1:
        BOT_TOKEN = lines[0].strip()
    if len(lines) >= 2:
        try:
            OWNER_ID = int(lines[1].strip())
        except Exception:
            OWNER_ID = None
# --- End secrets.txt reading ---

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.reactions = True

bot = commands.Bot(command_prefix='/', intents=intents, help_command=None, owner_id=OWNER_ID)
bot.start_time = None

@bot.event
async def on_ready():
    bot.start_time = datetime.now(UTC)
    print(f'Logged in as {bot.user}')
    await bot.tree.sync()
    print("Slash commands synced.")

    from cogs.review_views import ActiveReviewView, ReviewedTaskView, CreateReviewButtonView
    bot.add_view(ActiveReviewView())
    bot.add_view(ReviewedTaskView())
    bot.add_view(CreateReviewButtonView())

    statuses = [
        discord.CustomActivity(type=discord.ActivityType.custom, name="Tracking active reviews 📋"),
        discord.CustomActivity(type=discord.ActivityType.custom, name="Organizing tasks 🗂️"),
        discord.CustomActivity(type=discord.ActivityType.custom, name="Ready for your reviews! 🚀"),
        discord.CustomActivity(type=discord.ActivityType.custom, name="Helping you manage reviews! 🤖"),
        discord.CustomActivity(type=discord.ActivityType.custom, name="Making reviews easier! 🎉"),
        discord.CustomActivity(type=discord.ActivityType.custom, name="Your review assistant! 🤝"),
        discord.CustomActivity(type=discord.ActivityType.custom, name="Keeping track of tasks! 📊"),
        discord.CustomActivity(type=discord.ActivityType.custom, name="Reviewing with you! 🔍"),
    ]
    while True:
        for status in statuses:
            await bot.change_presence(activity=status)
            await asyncio.sleep(300)

async def setup_cogs():
    await bot.load_extension("cogs.review_modals")
    await bot.load_extension("cogs.review_views")
    await bot.load_extension("cogs.review_commands")
    await bot.load_extension("cogs.review_events")

if __name__ == '__main__':
    ensure_data_file()
    asyncio.run(setup_cogs())
    bot.run(BOT_TOKEN)