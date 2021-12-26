from datetime import datetime
from discord.commands import slash_command
from discord import Option
from utils import api
from views.selects import DropdownView
from views.buttons import PaginatorView, ReactionRoleView

import discord
import json


async def os_autocomplete(ctx: discord.AutocompleteContext) -> list: return [_ for _ in [*api.VALID_RELEASES, 'Other'] if _.lower().startswith(ctx.value.lower())]


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
            'timestamp': str(datetime.now()),
            'color': int(discord.Color.blurple()),
            'thumbnail': {
                'url': ctx.guild.icon.url
            },
            'fields': [
                    {
                        'name': os,
                        'value': f"Status: {'Enabled' if roles[os].get('enabled') else 'Disabled'}\nAnnouncement Channel: {ctx.guild.get_channel(roles[os].get('channel')).mention}\nAnnouncement Role: {ctx.guild.get_role(roles[os].get('role')).mention}",
                        'inline': False
                    } 
                for os in roles.keys()
            ],
            'footer': {
                'text': 'Apple Releases • Made by m1sta and Jaidan',
                'icon_url': str(self.bot.user.display_avatar.with_static_format('png').url)
            },
        }
        await ctx.respond(embed=discord.Embed.from_dict(embed), ephemeral=True)
        

    @config.command(name='setchannel', description='Set a channel for Apple releases to be announced in.')
    async def set_channel(self, ctx: discord.ApplicationContext, channel: Option(discord.TextChannel, 'Channel to send Apple releases in')):
        timeout_embed = discord.Embed(title='Add Device', description='No response given in 5 minutes, cancelling.')
        cancelled_embed = discord.Embed(title='Add Device', description='Cancelled.')
        invalid_embed = discord.Embed(title='Error')

        for x in (timeout_embed, cancelled_embed):
            x.set_footer(text=ctx.author.display_name, icon_url=ctx.author.display_avatar.with_static_format('png').url)

        if not ctx.author.guild_permissions.administrator:
            invalid_embed.description = 'You do not have permission to use this command.'
            await ctx.respond(embed=invalid_embed, ephemeral=True)
            return

        if not channel.can_send():
            invalid_embed.description = "I don't have permission to send Apple releases into that channel."
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
    async def toggle_release(self, ctx: discord.ApplicationContext, os: Option(str, description='Toggle announcing an Apple release', autocomplete=os_autocomplete)):
        invalid_embed = discord.Embed(title='Error')

        if not ctx.author.guild_permissions.administrator:
            invalid_embed.description = 'You do not have permission to use this command.'
            await ctx.respond(embed=invalid_embed, ephemeral=True)
            return

        if os not in api.VALID_RELEASES:
            invalid_embed.description = f'`{os}` is not a valid OS type.'
            await ctx.respond(embed=invalid_embed, ephemeral=True)
            return

        async with self.bot.db.execute('SELECT data FROM roles WHERE guild = ?', (ctx.guild.id,)) as cursor:
            roles = json.loads((await cursor.fetchone())[0])

        enabled = not roles[os].get('enabled')
        roles[os].update({'enabled': enabled})
        await self.bot.db.execute('UPDATE roles SET data = ? WHERE guild = ?', (json.dumps(roles), ctx.guild.id))
        await self.bot.db.commit()

        embed = discord.Embed(title='Configuration', description=f"{os} releases will {'now' if enabled else 'no longer'} be announced.")
        embed.set_footer(text=ctx.author.display_name, icon_url=ctx.author.display_avatar.with_static_format('png').url)

        await ctx.respond(embed=embed, ephemeral=True)

    @slash_command(description='Send a Reaction Role message for Apple Release announcements.')
    async def reactionrole(self, ctx: discord.ApplicationContext, channel: Option(discord.TextChannel, 'Channel to send Apple releases in', required=False)) -> None:
        if channel is None:
            channel = ctx.channel

        if not channel.can_send():
            embed = discord.Embed(title='Error', description="I don't have permission to send messages into that channel.")
            await ctx.respond(embed=embed, ephemeral=True)
            return

        async with self.bot.db.execute('SELECT data FROM roles WHERE guild = ?', (ctx.guild.id,)) as cursor:
            data = json.loads((await cursor.fetchone())[0])

        roles = [ctx.guild.get_role(data[_]['role']) for _ in data.keys()]

        buttons = [{
            'label': 'Invite',
            'style': discord.ButtonStyle.link,
            'url': self.utils.invite
        }]

        buttons = dict()
        for role in roles:
            buttons[role] = {
                'label': role.name,
                'style': discord.ButtonStyle.secondary,
                'custom_id': role.id
            }

        embed = discord.Embed(description='Click the buttons to opt in or out of Apple release notifications of your choice.')
        embed.set_thumbnail(url=self.bot.user.display_avatar.with_static_format('png').url)
        embed.set_footer(text='Apple Releases • Made by m1sta and Jaidan', icon_url=self.bot.user.display_avatar.with_static_format('png').url)

        await channel.send(embed=embed, view=ReactionRoleView(buttons))

        embed = discord.Embed(title='Reaction Role', description=f'Reaction Role embed sent to {channel.mention}.')
        embed.set_footer(text=ctx.author.display_name, icon_url=ctx.author.display_avatar.with_static_format('png').url)
        
        await ctx.respond(embed=embed, ephemeral=True)


def setup(bot):
    bot.add_cog(ConfigCog(bot))
