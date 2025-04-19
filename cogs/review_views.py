import discord
from discord.ui import View, Select, Button
from .review_utils import load_data, save_data, is_valid_url
from datetime import datetime, UTC

class RoleSelectView(View):
    def __init__(self, title, link, roles, selected_role_ids=None, page=0):
        super().__init__(timeout=60)
        self.title = title
        self.link = link
        self.roles = roles
        self.selected_role_ids = selected_role_ids or []
        self.page = page
        self.total_pages = (len(roles) + 24) // 25
        start = page * 25
        end = start + 25
        roles_page = roles[start:end]
        self.add_item(RoleSelect(self.title, self.link, roles, roles_page, self.selected_role_ids, self.page))
        if self.total_pages > 1:
            if self.page > 0:
                self.add_item(PrevPageButton(self.title, self.link, self.roles, self.selected_role_ids, self.page))
            if end < len(roles):
                self.add_item(NextPageButton(self.title, self.link, self.roles, self.selected_role_ids, self.page))
        self.add_item(DoneSelectingRolesButton(self.title, self.link, self.roles, self.selected_role_ids))

class RoleSelect(Select):
    def __init__(self, title, link, all_roles, roles_page, selected_role_ids, page):
        self.title = title
        self.link = link
        self.all_roles = all_roles
        self.roles_page = roles_page
        self.selected_role_ids = selected_role_ids
        self.page = page

        def role_option(role):
            if role.color.value == 0:
                emoji = "⚪"
            elif role.color.value < 0x555555:
                emoji = "⚫"
            elif role.color.value < 0xAA0000:
                emoji = "🔴"
            elif role.color.value < 0x00AA00:
                emoji = "🟢"
            elif role.color.value < 0x0000AA:
                emoji = "🔵"
            elif role.color.value < 0xAAAA00:
                emoji = "🟡"
            elif role.color.value < 0x00AAAA:
                emoji = "🟦"
            elif role.color.value < 0xAA00AA:
                emoji = "🟣"
            else:
                emoji = "🟠"
            return discord.SelectOption(
                label=f"{emoji} {role.name}",
                value=str(role.id),
                default=(str(role.id) in selected_role_ids)
            )

        super().__init__(
            placeholder=f"Select roles (page {page+1})",
            min_values=0,
            max_values=len(roles_page),
            options=[role_option(role) for role in roles_page]
        )

    async def callback(self, interaction: discord.Interaction):
        if not self.values:
            await interaction.response.defer()
            return
        new_selected = self.selected_role_ids + [role_id for role_id in self.values if role_id not in self.selected_role_ids]
        await interaction.response.edit_message(
            content=f"Roles selected: {len(new_selected)}. You can change page or finish selection.",
            view=RoleSelectView(self.title, self.link, self.all_roles, new_selected, self.page)
        )

class NextPageButton(Button):
    def __init__(self, title, link, all_roles, selected_role_ids, page):
        super().__init__(
            label="Next Page",
            style=discord.ButtonStyle.primary,
            row=1
        )
        self.title = title
        self.link = link
        self.all_roles = all_roles
        self.selected_role_ids = selected_role_ids
        self.page = page

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(
            content=f"Select more roles for this review (page {self.page+2}):",
            view=RoleSelectView(self.title, self.link, self.all_roles, self.selected_role_ids, self.page + 1)
        )

class PrevPageButton(Button):
    def __init__(self, title, link, all_roles, selected_role_ids, page):
        super().__init__(
            label="Previous Page",
            style=discord.ButtonStyle.secondary,
            row=1
        )
        self.title = title
        self.link = link
        self.all_roles = all_roles
        self.selected_role_ids = selected_role_ids
        self.page = page

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(
            content=f"Select more roles for this review (page {self.page}):",
            view=RoleSelectView(self.title, self.link, self.all_roles, self.selected_role_ids, self.page - 1)
        )

class DoneSelectingRolesButton(Button):
    def __init__(self, title, link, all_roles, selected_role_ids):
        super().__init__(
            label="Done selecting roles",
            style=discord.ButtonStyle.secondary,
            row=1
        )
        self.title = title
        self.link = link
        self.all_roles = all_roles
        self.selected_role_ids = selected_role_ids

    async def callback(self, interaction: discord.Interaction):
        selected_roles = [interaction.guild.get_role(int(role_id)) for role_id in self.selected_role_ids]
        from .review_commands import create_review_from_modal
        await create_review_from_modal(
            interaction, self.title, selected_roles, self.link
        )
        await interaction.response.edit_message(
            content=":white_check_mark: **Task submitted for review.**",
            view=None, delete_after=0
        )

class ActiveReviewView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Mark as Reviewed", style=discord.ButtonStyle.green, custom_id="mark_reviewed")
    async def mark_reviewed(self, interaction: discord.Interaction, button: discord.ui.Button):
        message_id = interaction.message.id
        data = load_data()
        guild_id = str(interaction.guild_id)
        guild_data = data.get(guild_id, {})
        review = guild_data.get('reviews', {}).get(str(message_id))
        allowed_role_ids = set()
        if review:
            if 'role_ids' in review:
                allowed_role_ids = set(review['role_ids'])
            elif 'role_id' in review and review['role_id']:
                allowed_role_ids = {review['role_id']}
        is_author = review and review['author_id'] == interaction.user.id
        has_role = any(role.id in allowed_role_ids for role in interaction.user.roles) if allowed_role_ids else False
        if not (is_author or has_role):
            await interaction.response.send_message(
                ":no_entry: **Only the author or a user with the selected role(s) can mark this as reviewed.**",
                ephemeral=True, delete_after=5
            )
            return
        if review and review['status'] == 'active':
            await interaction.message.delete()
            embed = interaction.message.embeds[0]
            embed.color = discord.Color.green()
            embed.add_field(name="Reviewed by", value=f'<@{interaction.user.id}>', inline=False)
            reviewed_channel_id = guild_data.get('reviewed_channel_id')
            reviewed_channel = interaction.client.get_channel(reviewed_channel_id)
            if reviewed_channel:
                new_msg = await reviewed_channel.send(embed=embed, view=ReviewedTaskView())
                del guild_data['reviews'][str(message_id)]
                guild_data['reviews'][str(new_msg.id)] = {
                    'title': review['title'],
                    'role_ids': review.get('role_ids', []),
                    'link': review.get('link'),
                    'author_id': review['author_id'],
                    'timestamp': review['timestamp'],
                    'status': 'reviewed',
                    'reviewed_by': interaction.user.id,
                    'dm_message_id': None
                }
                author = interaction.client.get_user(review['author_id'])
                if author:
                    reviewer_mention = f"<@{interaction.user.id}>"
                    dm_message = f"Your task '{review['title']}' has been reviewed by {reviewer_mention}. You can view it here: {new_msg.jump_url}"
                    try:
                        dm_msg = await author.send(dm_message)
                        guild_data['reviews'][str(new_msg.id)]['dm_message_id'] = dm_msg.id
                    except discord.Forbidden:
                        pass
                data[guild_id] = guild_data
                save_data(data)
            else:
                print(f"Reviewed channel not found in guild {guild_id}")
        await interaction.response.defer()

    @discord.ui.button(label="Delete", style=discord.ButtonStyle.red, custom_id="delete_active_task")
    async def delete_active_task(self, interaction: discord.Interaction, button: discord.ui.Button):
        message_id = interaction.message.id
        data = load_data()
        guild_id = str(interaction.guild_id)
        guild_data = data.get(guild_id, {})
        review = guild_data.get('reviews', {}).get(str(message_id))
        if not review:
            await interaction.response.send_message(
                ":warning: **Task not found.**", ephemeral=True, delete_after=5
            )
            return
        if review['author_id'] != interaction.user.id:
            await interaction.response.send_message(
                ":no_entry: **Only the user who created this task can delete it.**",
                ephemeral=True, delete_after=5
            )
            return
        await interaction.message.delete()
        del guild_data['reviews'][str(message_id)]
        data[guild_id] = guild_data
        save_data(data)
        await interaction.response.send_message(
            ":wastebasket: **Your task has been deleted.**", ephemeral=True, delete_after=5
        )

class ReviewedTaskView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Move Back", style=discord.ButtonStyle.blurple, custom_id="move_back")
    async def move_back(self, interaction: discord.Interaction, button: discord.ui.Button):
        message_id = interaction.message.id
        data = load_data()
        guild_id = str(interaction.guild_id)
        guild_data = data.get(guild_id, {})
        review = guild_data.get('reviews', {}).get(str(message_id))
        if review and review['status'] == 'reviewed':
            author = interaction.client.get_user(review['author_id'])
            dm_message_id = review.get('dm_message_id')
            if author and dm_message_id:
                try:
                    dm_channel = await author.create_dm()
                    dm_message = await dm_channel.fetch_message(dm_message_id)
                    await dm_message.delete()
                except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                    pass
            await interaction.message.delete()
            embed = interaction.message.embeds[0]
            for i, field in enumerate(embed.fields):
                if field.name == "Reviewed by":
                    embed.remove_field(i)
                    break
            embed.color = discord.Color.red()
            if review.get('role_ids'):
                roles = [interaction.guild.get_role(rid) for rid in review['role_ids']]
                for i, field in enumerate(embed.fields):
                    if field.name == "**Roles**":
                        embed.remove_field(i)
                        break
                embed.add_field(name="**Roles**", value=" ".join(role.mention for role in roles if role), inline=False)
            active_channel_id = guild_data.get('active_channel_id')
            active_channel = interaction.client.get_channel(active_channel_id)
            if active_channel:
                new_msg = await active_channel.send(embed=embed, view=ActiveReviewView())
                del guild_data['reviews'][str(message_id)]
                guild_data['reviews'][str(new_msg.id)] = {
                    'title': review['title'],
                    'role_ids': review.get('role_ids', []),
                    'link': review.get('link'),
                    'author_id': review['author_id'],
                    'timestamp': review['timestamp'],
                    'status': 'active'
                }
                data[guild_id] = guild_data
                save_data(data)
            else:
                print(f"Active channel not found in guild {guild_id}")
        await interaction.response.defer()

    @discord.ui.button(label="Delete", style=discord.ButtonStyle.red, custom_id="delete_task")
    async def delete_task(self, interaction: discord.Interaction, button: discord.ui.Button):
        message_id = interaction.message.id
        data = load_data()
        guild_id = str(interaction.guild_id)
        guild_data = data.get(guild_id, {})
        review = guild_data.get('reviews', {}).get(str(message_id))
        if review and review['status'] == 'reviewed':
            author = interaction.client.get_user(review['author_id'])
            dm_message_id = review.get('dm_message_id')
            if author and dm_message_id:
                try:
                    dm_channel = await author.create_dm()
                    dm_message = await dm_channel.fetch_message(dm_message_id)
                    await dm_message.delete()
                except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                    pass
            await interaction.message.delete()
            del guild_data['reviews'][str(message_id)]
            data[guild_id] = guild_data
            save_data(data)
        await interaction.response.defer()

class CreateReviewButtonView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Create Review", style=discord.ButtonStyle.primary, custom_id="open_review_modal")
    async def open_review_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        from .review_modals import CreateReviewModal
        await interaction.response.send_modal(CreateReviewModal())

async def setup(bot):
    pass
