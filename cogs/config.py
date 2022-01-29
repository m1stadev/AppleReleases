# imports
from discord import Option
from discord.commands import slash_command
from utils import api
from views.selects import DropdownView
from views.buttons import PaginatorView, ReactionRoleButton

import discord
import json

async def release_autocomplete(ctx: discord.AutocompleteContext) -> list: return [_ for _ in [*api.VALID_RELEASES, 'Other'] if ctx.value.lower() in _.lower()]

class ConfigCog(discord.Cog, name='Configuration'):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

        self.utils = self.bot.get_cog('Utilities')

    config = discord.SlashCommandGroup('config', 'Configuration commands')

    @config.command(name='help', description='View all configuration commands.')
    async def _help(self, ctx: discord.ApplicationContext) -> None:
        cmd_embeds = [await self.utils.cmd_help_embed(ctx, _) for _ in self.config.subcommands]

        paginator = PaginatorView(cmd_embeds, ctx, timeout=180)
        await ctx.respond(embed=cmd_embeds[paginator.embed_num], view=paginator, ephemeral=True)
    
    @config.command(name='list', description='List current configuration settings.')
    async def list_config(self, ctx: discord.ApplicationContext) -> None:
        async with self.bot.db.execute('SELECT data FROM roles WHERE guild = ?', (ctx.guild_id,)) as cursor:
            roles = json.loads((await cursor.fetchone())[0])

        embed = {
            'title': 'Apple Releases Configuration',
            'color': int(discord.Color.blurple()),
            'thumbnail': {
                'url': ctx.guild.icon.url
            },
            'fields': [
                    {
                        'name': os,
                        'value': f"Status: **{'Enabled' if roles[os].get('enabled') else 'Disabled'}**\nAnnouncement Channel: {ctx.guild.get_channel(roles[os].get('channel')).mention if ctx.guild.get_channel(roles[os].get('channel')) is not None else 'None'}\nAnnouncement Role: {ctx.guild.get_role(roles[os].get('role')).mention}",
                        'inline': False
                    } 
                for os in roles.keys()
            ],
            'footer': {
                'text': 'Apple Releases • Made by m1sta and Jaidan',
                'icon_url': str(self.bot.user.display_avatar.with_static_format('png').url)
            },
        }

        other = next(embed['fields'].index(_) for _ in embed['fields'] if _['name'] == 'Other')
        embed['fields'][other]['name'] = embed['fields'][other]['name'] + ' (*Xcode, TestFlight, App Store Connect, etc.*)'

        await ctx.respond(embed=discord.Embed.from_dict(embed), ephemeral=False)

    @config.command(name='setchannel', description='Set a channel for Apple releases to be announced in.')
    async def set_channel(self, ctx: discord.ApplicationContext, channel: Option(discord.TextChannel, 'Channel to send Apple releases in', required=False)):
        timeout_embed = discord.Embed(title='Add Device', description='No response given in 5 minutes, cancelling.')
        cancelled_embed = discord.Embed(title='Add Device', description='Cancelled.')
        invalid_embed = discord.Embed(title='Error')

        for x in (timeout_embed, cancelled_embed):
            x.set_footer(text=ctx.author.display_name, icon_url=ctx.author.display_avatar.with_static_format('png').url)

        if not ctx.author.guild_permissions.manage_guild:
            invalid_embed.description = 'You do not have permission to use this command.'
            await ctx.respond(embed=invalid_embed, ephemeral=True)
            return

        if channel is None:
            channel = ctx.channel

        if not channel.can_send():
            invalid_embed.description = f"I don't have permission to send messages into {channel.mention}."
            await ctx.respond(embed=invalid_embed, ephemeral=True)
            return

        async with self.bot.db.execute('SELECT data FROM roles WHERE guild = ?', (ctx.guild.id,)) as cursor:
            roles = json.loads((await cursor.fetchone())[0])

        options = [
            discord.SelectOption(
                label='All',
                description='All Apple releases'
            )
        ]

        for os in roles.keys():
            options.append(discord.SelectOption(
                label=os,
                description=f'All {os} releases'
            ))

        options.append(discord.SelectOption(
            label='Cancel',
            emoji='❌'
        ))

        embed = discord.Embed(title='Configuration', description=f"Choose which software you'd like to announce new releases in {channel.mention} for.")
        embed.set_footer(text=ctx.author.display_name, icon_url=ctx.author.display_avatar.with_static_format('png').url)

        dropdown = DropdownView(options, ctx, 'Software')
        await ctx.respond(embed=embed, view=dropdown, ephemeral=True)
        await dropdown.wait()
        if dropdown.answer is None:
            await ctx.edit(embed=timeout_embed)
            return

        elif dropdown.answer == 'Cancel':
            await ctx.edit(embed=cancelled_embed)
            return

        if dropdown.answer == 'All':
            for os in roles.keys():
                roles[os].update({'channel': channel.id})

        else:
            roles[dropdown.answer].update({'channel': channel.id})

        await self.bot.db.execute('UPDATE roles SET data = ? WHERE guild = ?', (json.dumps(roles), ctx.guild.id))
        await self.bot.db.commit()

        embed = discord.Embed(title='Configuration', description=f"All {'Apple' if dropdown.answer == 'All' else dropdown.answer} releases will now be announced in: {channel.mention}")
        embed.set_footer(text=ctx.author.display_name, icon_url=ctx.author.display_avatar.with_static_format('png').url)

        await ctx.edit(embed=embed)

    @config.command(name='toggle', description='Toggle the announcement of Apple releases.')
    async def toggle_release(self, ctx: discord.ApplicationContext, release: Option(str, description='Apple release to toggle', autocomplete=release_autocomplete)):
        invalid_embed = discord.Embed(title='Error')

        if not ctx.author.guild_permissions.manage_guild:
            invalid_embed.description = 'You do not have permission to use this command.'
            await ctx.respond(embed=invalid_embed, ephemeral=True)
            return

        if release not in [*api.VALID_RELEASES, 'Other']:
            invalid_embed.description = f'`{release}` is not a valid OS type.'
            await ctx.respond(embed=invalid_embed, ephemeral=True)
            return

        async with self.bot.db.execute('SELECT data FROM roles WHERE guild = ?', (ctx.guild.id,)) as cursor:
            roles = json.loads((await cursor.fetchone())[0])

        enabled = not roles[release].get('enabled')
        roles[release].update({'enabled': enabled})
        await self.bot.db.execute('UPDATE roles SET data = ? WHERE guild = ?', (json.dumps(roles), ctx.guild.id))
        await self.bot.db.commit()

        embed = discord.Embed(title='Configuration', description=f"**{release}** releases will {'now' if enabled else 'no longer'} be announced.")
        embed.set_footer(text=ctx.author.display_name, icon_url=ctx.author.display_avatar.with_static_format('png').url)

        await ctx.respond(embed=embed, ephemeral=True)

    @slash_command(name='reactionrole', description='Send a Reaction Role message for Apple Release announcements.')
    async def reaction_role(self, ctx: discord.ApplicationContext, channel: Option(discord.TextChannel, 'Channel to send Apple releases in', required=False)) -> None:
        invalid_embed = discord.Embed(title='Error')
        if not ctx.author.guild_permissions.manage_guild:
            invalid_embed.description = 'You do not have permission to use this command.'
            await ctx.respond(embed=invalid_embed, ephemeral=True)
            return

        if channel is None:
            channel = ctx.channel

        if not channel.can_send():
            invalid_embed.description = f"I don't have permission to send messages into {channel.mention}."
            await ctx.respond(embed=invalid_embed, ephemeral=True)
            return

        async with self.bot.db.execute('SELECT data FROM roles WHERE guild = ?', (ctx.guild.id,)) as cursor:
            data = json.loads((await cursor.fetchone())[0])

        view = discord.ui.View(timeout=None)
        roles = [ctx.guild.get_role(data[_]['role']) for _ in data.keys()]
        for role in roles:
            view.add_item(ReactionRoleButton(role, row=0 if roles.index(role) < 3 else 1))

        embed = discord.Embed(description='Click the buttons to opt in or out of Apple release notifications of your choice.')
        embed.set_thumbnail(url=self.bot.user.display_avatar.with_static_format('png').url)
        embed.set_footer(text='Apple Releases • Made by m1sta and Jaidan', icon_url=self.bot.user.display_avatar.with_static_format('png').url)

        await channel.send(embed=embed, view=view)

        embed = discord.Embed(title='Reaction Role', description=f'Reaction Role embed sent to {channel.mention}.')
        embed.set_footer(text=ctx.author.display_name, icon_url=ctx.author.display_avatar.with_static_format('png').url)
        
        await ctx.respond(embed=embed, ephemeral=True)

def setup(bot):
    bot.add_cog(ConfigCog(bot))
