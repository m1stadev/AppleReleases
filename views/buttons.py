from typing import Mapping, Optional

import discord


class SelectButton(discord.ui.Button['SelectView']):
    def __init__(self, button: dict):
        super().__init__(**button)

        self.button_type = button['label']

    async def callback(self, interaction: discord.Interaction):
        self.view.answer = self.button_type
        await self.view.on_timeout()
        self.view.stop()


class SelectView(discord.ui.View):
    def __init__(self, buttons: list[dict], context: Optional[discord.ApplicationContext], *, public: bool=False, timeout: int=60):
        super().__init__(timeout=timeout)

        self.ctx = context
        self.public = public
        self.answer = None

        for button in buttons:
            self.add_item(SelectButton(button))

    async def interaction_check(self, interaction: discord.Interaction):
        if self.public == True or interaction.channel.type == discord.ChannelType.private:
            return True

        return interaction.user == self.ctx.author

    async def on_timeout(self):
        self.clear_items()
        if self.ctx is not None:
            await self.ctx.edit(view=self)


class PaginatorButton(discord.ui.Button['PaginatorView']):
    def __init__(self, emoji: str, disabled: bool):
        super().__init__(
            emoji=emoji,
            style=discord.ButtonStyle.secondary,
            disabled=disabled
        )

    async def callback(self, interaction: discord.Interaction):
        if self == self.view.children[0]:
            self.view.embed_num = 0
        elif self == self.view.children[1]:
            self.view.embed_num -= 1
        elif self == self.view.children[2]:
            self.view.embed_num += 1
        elif self == self.view.children[3]:
            self.view.embed_num = len(self.view.embeds) - 1

        await self.view.update_view()

class PaginatorView(discord.ui.View):
    def __init__(self, embeds: list[discord.Embed], context: discord.ApplicationContext, *, public: bool=False, timeout: int=60):
        super().__init__(timeout=timeout)

        self.ctx = context
        self.public = public
        self.embeds = embeds
        self.embed_num = 0

        for emoji in ('⏪', '⬅️', '➡️', '⏩'):
            disabled = False if (emoji == '➡️') or (emoji == '⏩' and len(self.embeds) >= 3) else True
            self.add_item(PaginatorButton(emoji, disabled))

    async def update_view(self):
        self.children[0].disabled = False if self.embed_num > 1 else True
        self.children[1].disabled = False if self.embed_num > 0 else True
        self.children[2].disabled = False if self.embed_num < (len(self.embeds) - 1) else True
        self.children[3].disabled = False if self.embed_num < (len(self.embeds) - 2) else True

        await self.ctx.edit(embed=self.embeds[self.embed_num], view=self)

    async def interaction_check(self, interaction: discord.Interaction):
        if self.public == True or interaction.channel.type == discord.ChannelType.private:
            return True

        return interaction.user == self.ctx.author

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True

        await self.ctx.edit(view=self)


class ReactionRoleButton(discord.ui.Button):
    def __init__(self, role: discord.Role, *, row=0):
        super().__init__(
            label=role.name,
            style=discord.ButtonStyle.primary,
            custom_id=str(role.id),
            row=row
        )

        self.role = role

    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(title='Apple Releases')

        if self.role not in interaction.user.roles:
            await interaction.user.add_roles(self.role, reason='Added by Apple Releases')
            embed.description = f'You have been given the **{self.role.name}** role.'
        else:
            await interaction.user.remove_roles(self.role, reason='Removed by Apple Releases')
            embed.description = f'You have removed the **{self.role.name}** role.'

        await interaction.response.send_message(embed=embed, ephemeral=True)
