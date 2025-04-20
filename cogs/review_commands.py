import discord
from discord.ext import commands
from discord import app_commands
from .review_utils import is_valid_url, load_data, save_data
from .review_views import RoleSelectView, CreateReviewButtonView, ActiveReviewView
from .review_modals import DeleteConfirmationModal, CreateReviewModal
from datetime import datetime, UTC, timedelta
import asyncio
import json
import os

def format_timedelta(td):
    days = td.days
    hours, rem = divmod(td.seconds, 3600)
    minutes, seconds = divmod(rem, 60)
    parts = []
    if days: parts.append(f"{days}d")
    if hours: parts.append(f"{hours}h")
    if minutes: parts.append(f"{minutes}m")
    if seconds or not parts: parts.append(f"{seconds}s")
    return " ".join(parts)

class ReviewCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Shows help for bot commands")
    async def help_command(self, interaction: discord.Interaction):
        is_admin = False
        if interaction.guild:
            member = interaction.guild.get_member(interaction.user.id)
            is_admin = member.guild_permissions.administrator if member else False

        embed = discord.Embed(
            title="🤖 **Review Bot Guide**",
            description=(
                "Welcome to the Review Bot!\n\n"
                "This bot helps you manage code/task reviews in your server.\n"
                "Use the commands below to get started."
            ),
            color=discord.Color.blurple()
        )
        if is_admin:
            embed.add_field(
                name=":hammer_pick: `/create`",
                value="Create the **active-reviews** and **reviewed-tasks** channels for managing tasks. *(Admin only)*",
                inline=False
            )
        embed.add_field(
            name=":pencil: `/review`",
            value=(
                "Submit a task for review.\n"
                "**Usage:** `/review title: \"Task Title\" role: @Role link: \"URL\"`\n"
                "- `role` and `link` are optional.\n"
                "- You can also use the **Create Review** button in the active-reviews channel."
            ),
            inline=False
        )
        if is_admin:
            embed.add_field(
                name=":wastebasket: `/delete`",
                value="Delete the review channels after confirmation. *(Admin only)*",
                inline=False
            )
        embed.set_footer(text="Need more help? Contact your server admin or use /help again.")
        try:
            await interaction.user.send(embed=embed)
            await interaction.response.send_message("📬 **Check your DMs for the Review Bot guide!**", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=30)

    @app_commands.command(name="create", description="Create two new channels for active and reviewed tasks")
    @app_commands.default_permissions(administrator=True)
    async def create_channels(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild_id = str(interaction.guild_id)
        data = load_data()
        if guild_id in data:
            await interaction.followup.send(embed=discord.Embed(
                description=":warning: **Review channels already exist for this server.**\nUse `/delete` to remove them first.",
                color=discord.Color.red()), ephemeral=True)
            return
        active_overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(send_messages=True, use_application_commands=True),
            interaction.guild.me: discord.PermissionOverwrite(send_messages=True, manage_messages=True)
        }
        reviewed_overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(send_messages=False, use_application_commands=False),
            interaction.guild.me: discord.PermissionOverwrite(send_messages=True, manage_messages=True)
        }
        try:
            active_channel = await interaction.guild.create_text_channel('active-reviews', overwrites=active_overwrites)
            reviewed_channel = await interaction.guild.create_text_channel('reviewed-tasks', overwrites=reviewed_overwrites)
        except discord.Forbidden:
            await interaction.followup.send(embed=discord.Embed(
                description="⚠️ Failed to create channels. Please check bot permissions.",
                color=discord.Color.red()), ephemeral=True)
            return
        data[guild_id] = {
            "active_channel_id": active_channel.id,
            "reviewed_channel_id": reviewed_channel.id,
            "reviews": {}
        }
        save_data(data)
        try:
            await active_channel.edit(topic="Post review requests here. Use the 'Mark as Reviewed' button to move tasks.")
            await reviewed_channel.edit(topic="Reviewed tasks are moved here. Use 'Move Back' or 'Delete' buttons to manage.")
        except discord.Forbidden:
            print(f"Failed to set channel topics in guild {guild_id} due to permissions.")
        active_embed = discord.Embed(
            title="📋 **Active Reviews**",
            description=(
                "Welcome to **Active Reviews**!\n\n"
                "➡️ Use `/review` or the **Create Review** button below to submit a task for review.\n"
                "✅ When a task is ready, click **Mark as Reviewed** to move it to the reviewed-tasks channel.\n\n"
                "🔒 Only the author or selected roles can mark a task as reviewed.\n"
                "ℹ️ For help, use `/help` or check the pinned message."
            ),
            color=discord.Color.blurple()
        )
        active_embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar.url)
        reviewed_embed = discord.Embed(
            title="✅ **Reviewed Tasks**",
            description=(
                "This channel contains tasks that have been **reviewed** and are considered complete.\n\n"
                "⬅️ To move a task back to active reviews, click **Move Back**.\n"
                "🗑️ To permanently delete a task, click **Delete**.\n\n"
                ":no_entry: *You cannot send messages in this channel. Only button interactions are allowed.*\n"
                "ℹ️ For help, use `/help` or check the pinned message."
            ),
            color=discord.Color.green()
        )
        reviewed_embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar.url)
        try:
            active_msg = await active_channel.send(
                embed=active_embed,
                view=CreateReviewButtonView()
            )
            await active_msg.pin()
        except discord.Forbidden:
            print(f"Failed to send or pin message in active-reviews channel in guild {guild_id} due to permissions.")
        try:
            reviewed_msg = await reviewed_channel.send(embed=reviewed_embed)
            await reviewed_msg.pin()
        except discord.Forbidden:
            print(f"Failed to send or pin message in reviewed-tasks channel in guild {guild_id} due to permissions.")

        await interaction.followup.send(embed=discord.Embed(
            description=":white_check_mark: **Created 'active-reviews' and 'reviewed-tasks' channels with explanatory messages.**",
            color=discord.Color.green()), ephemeral=True)

    @app_commands.command(name="review", description="Submit a task for review")
    @app_commands.describe(
        title="The title of the task",
        role="The role to assign to the task (optional)",
        link="A URL related to the task (optional)"
    )
    async def review_task(self, interaction: discord.Interaction, title: str, role: discord.Role = None, link: str = None):
        guild_id = str(interaction.guild_id)
        data = load_data()
        guild_data = data.get(guild_id, {})
        active_channel_id = guild_data.get('active_channel_id')
        if link and not is_valid_url(link):
            await interaction.response.send_message(embed=discord.Embed(
                description=":warning: **The provided link is not a valid URL. Please use a link starting with `http://` or `https://`.**",
                color=discord.Color.red()), ephemeral=True)
            return
        if not active_channel_id:
            await interaction.response.send_message(embed=discord.Embed(
                description=":warning: **No active review channel found.**\nPlease create one using `/create`.",
                color=discord.Color.red()), ephemeral=True)
            return
        active_channel = self.bot.get_channel(active_channel_id)
        if not active_channel:
            await interaction.response.send_message(embed=discord.Embed(
                description=":warning: **Could not access the active review channel.**\nPlease check bot permissions.",
                color=discord.Color.red()), ephemeral=True)
            return
        embed = discord.Embed(
            title=f"📝 **{title}**",
            color=discord.Color.orange(),
            timestamp=datetime.now(UTC)
        )
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.avatar.url)
        if role:
            embed.add_field(name="**Role**", value=role.mention, inline=False)
        if link:
            embed.add_field(name="**Link**", value=f"[Click here]({link})", inline=False)
        review_msg = await active_channel.send(embed=embed, view=ActiveReviewView())
        guild_data.setdefault('reviews', {})[str(review_msg.id)] = {
            'title': title,
            'role_id': role.id if role else None,
            'link': link,
            'author_id': interaction.user.id,
            'timestamp': review_msg.created_at.isoformat(),
            'status': 'active'
        }
        data[guild_id] = guild_data
        save_data(data)
        await interaction.response.send_message(":white_check_mark: **Task submitted for review in the active-reviews channel.**", ephemeral=True)
        if active_channel_id == interaction.channel_id:
            await asyncio.sleep(10)
            try:
                await interaction.delete_original_response()
            except discord.HTTPException:
                pass

    @app_commands.command(name="delete", description="Delete the active-reviews and reviewed-tasks channels after confirmation")
    @app_commands.default_permissions(administrator=True)
    async def delete_channels(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild_id)
        data = load_data()
        guild_data = data.get(guild_id, {})
        active_channel_id = guild_data.get('active_channel_id')
        reviewed_channel_id = guild_data.get('reviewed_channel_id')
        if not guild_data or (active_channel_id is None and reviewed_channel_id is None):
            await interaction.response.send_message(embed=discord.Embed(
                description="There are no review channels to delete.",
                color=discord.Color.red()), ephemeral=True)
            return
        modal = DeleteConfirmationModal()
        await interaction.response.send_modal(modal)

    @commands.command(name="status")
    @commands.is_owner()
    async def status(self, ctx):
        """Show bot uptime and GitHub webhook info (owner only)."""
        now = datetime.now(UTC)
        uptime = now - (self.bot.start_time or now)
        embed = discord.Embed(
            title="Bot Status",
            color=discord.Color.blurple()
        )
        embed.add_field(name="Uptime", value=format_timedelta(uptime), inline=False)

        # Read last GitHub update info from file
        update_file = os.path.join(os.path.dirname(__file__), "..", "last_github_update.json")
        try:
            with open(update_file, "r") as f:
                update_info = json.load(f)
            last_pull = update_info.get("pulled_at", "Unknown")
            commit_msg = update_info.get("commit_message", "Unknown")
            commit_hash = update_info.get("commit_hash", "Unknown")
            commit_author = update_info.get("commit_author", "Unknown")
        except Exception:
            last_pull = "Unknown"
            commit_msg = "Unknown"
            commit_hash = "Unknown"
            commit_author = "Unknown"

        embed.add_field(
            name="Last Git Pull",
            value=f"{last_pull}",
            inline=False
        )
        embed.add_field(
            name="Latest Commit",
            value=f"`{commit_hash}` by **{commit_author}**\n{commit_msg}",
            inline=False
        )
        embed.set_footer(text="Only visible to the bot owner.")
        await ctx.send(embed=embed)

async def create_review_from_modal(interaction, title, roles, link):
    guild_id = str(interaction.guild_id)
    data = load_data()
    guild_data = data.get(guild_id, {})
    active_channel_id = guild_data.get('active_channel_id')
    if not active_channel_id:
        await interaction.followup.send(
            embed=discord.Embed(
                description=":warning: **No active review channel found.**\nPlease create one using `/create`.",
                color=discord.Color.red()
            ),
            ephemeral=True
        )
        return
    active_channel = interaction.client.get_channel(active_channel_id)
    if not active_channel:
        await interaction.followup.send(
            embed=discord.Embed(
                description=":warning: **Could not access the active review channel.**\nPlease check bot permissions.",
                color=discord.Color.red()
            ),
            ephemeral=True
        )
        return
    embed = discord.Embed(
        title=f"📝 **{title}**",
        color=discord.Color.orange(),
        timestamp=datetime.now(UTC)
    )
    embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.avatar.url)
    if roles and len(roles) > 0:
        embed.add_field(name="**Roles**", value=" ".join(role.mention for role in roles if role), inline=False)
    if link:
        embed.add_field(name="**Link**", value=f"[Click here]({link})", inline=False)
    review_msg = await active_channel.send(embed=embed, view=ActiveReviewView())
    guild_data.setdefault('reviews', {})[str(review_msg.id)] = {
        'title': title,
        'role_ids': [role.id for role in roles] if roles else [],
        'link': link,
        'author_id': interaction.user.id,
        'timestamp': review_msg.created_at.isoformat(),
        'status': 'active'
    }
    data[guild_id] = guild_data
    save_data(data)

async def setup(bot):
    await bot.add_cog(ReviewCommands(bot))
