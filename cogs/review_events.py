from discord.ext import commands
from .review_utils import load_data
import discord

class ReviewEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        data = load_data()
        guild_id = str(message.guild.id)
        guild_data = data.get(guild_id, {})
        active_channel_id = guild_data.get('active_channel_id')
        reviewed_channel_id = guild_data.get('reviewed_channel_id')
        if message.channel.id == active_channel_id:
            await message.delete()
            await message.channel.send(embed=discord.Embed(
                description=":warning: **Please use the `/review` slash command to create a review.**",
                color=discord.Color.red()), delete_after=10)
        elif message.channel.id == reviewed_channel_id:
            await message.delete()
            await message.channel.send(embed=discord.Embed(
                description=":no_entry: **No messages are allowed in this channel.**",
                color=discord.Color.red()), delete_after=10)

async def setup(bot):
    await bot.add_cog(ReviewEvents(bot))
