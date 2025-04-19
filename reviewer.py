import discord
from discord.ext import commands
import os
import json
import asyncio

DATA_FILE = 'reviews.json'

def ensure_data_file():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'w') as f:
            json.dump({}, f, indent=4)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.reactions = True

bot = commands.Bot(command_prefix='/', intents=intents, help_command=None)

@bot.event
async def on_ready():
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
    token = open('token.txt').readline().strip()
    bot.run(token)