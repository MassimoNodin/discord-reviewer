import discord
from discord.ui import Modal, TextInput
from .review_utils import is_valid_url, load_data, save_data

class DeleteConfirmationModal(Modal):
    def __init__(self):
        super().__init__(title="Confirm Deletion")
        self.add_item(TextInput(
            label="Type 'confirm' to delete the channels",
            placeholder="Type 'confirm' here",
            required=True,
            style=discord.TextStyle.short
        ))

    async def on_submit(self, interaction: discord.Interaction):
        user_input = self.children[0].value.strip().lower()
        if user_input == "confirm":
            guild_id = str(interaction.guild_id)
            data = load_data()
            guild_data = data.get(guild_id, {})
            active_channel_id = guild_data.get('active_channel_id')
            reviewed_channel_id = guild_data.get('reviewed_channel_id')
            active_channel = interaction.client.get_channel(active_channel_id)
            reviewed_channel = interaction.client.get_channel(reviewed_channel_id)
            try:
                if active_channel:
                    await active_channel.delete()
                if reviewed_channel:
                    await reviewed_channel.delete()
                if guild_id in data:
                    del data[guild_id]
                save_data(data)
                await interaction.response.defer()
            except discord.Forbidden:
                error_embed = discord.Embed(
                    title="Permission Error",
                    description="⚠️ I don't have permission to delete channels.",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=error_embed, ephemeral=True)
        else:
            cancel_embed = discord.Embed(
                title="Deletion Cancelled",
                description="You did not type 'confirm'. The deletion has been cancelled.",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=cancel_embed, ephemeral=True)

class CreateReviewModal(Modal):
    def __init__(self):
        super().__init__(title="Submit a Review")
        self.title_input = TextInput(
            label="Task Title",
            placeholder="Enter the title of the task",
            required=True,
            style=discord.TextStyle.short,
            max_length=200
        )
        self.link_input = TextInput(
            label="Task Link (optional)",
            placeholder="Paste a URL (http/https) or leave blank",
            required=False,
            style=discord.TextStyle.short,
            max_length=2048
        )
        self.add_item(self.title_input)
        self.add_item(self.link_input)

    async def on_submit(self, interaction: discord.Interaction):
        from .review_views import RoleSelectView
        title = self.title_input.value.strip()
        link = self.link_input.value.strip() if self.link_input.value else None
        if link and not is_valid_url(link):
            await interaction.response.send_message(
                embed=discord.Embed(
                    description=":warning: **The provided link is not a valid URL. Please use a link starting with `http://` or `https://`.**",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )
            return
        roles = [
            role for role in interaction.guild.roles
            if not role.is_default()
        ]
        await interaction.response.send_message(
            "Select roles for this review (optional):",
            view=RoleSelectView(title, link, roles),
            ephemeral=True
        )

async def setup(bot):
    pass
