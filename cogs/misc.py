# imports
from datetime import datetime
from discord.commands import slash_command
from discord.ext import commands
from discord.utils import format_dt
from math import floor
from views.buttons import SelectView

import asyncio
import discord
import psutil
import sys

class MiscCog(commands.Cog, name='Miscellaneous'):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        self.utils = self.bot.get_cog('Utilities')
        psutil.cpu_percent() # Run once

    @slash_command(description='Get the invite for Apple Releases.')
    async def invite(self, ctx: discord.ApplicationContext) -> None:
        buttons = [{
            'label': 'Invite',
            'style': discord.ButtonStyle.link,
            'url': self.utils.invite
        }]

        embed = discord.Embed(title='Invite', description='Apple Releases invite:')
        embed.set_thumbnail(url=self.bot.user.display_avatar.with_static_format('png').url)
        embed.set_footer(text='Apple Releases • Made by m1sta and Jaidan', icon_url=self.bot.user.display_avatar.with_static_format('png').url)

        view = SelectView(buttons, ctx, timeout=None)
        await ctx.respond(embed=embed, view=view, ephemeral=True)

    @slash_command(description="See Apple Releases's latency.")
    async def ping(self, ctx: discord.ApplicationContext) -> None:
        embed = discord.Embed(title='Pong!', description='Testing ping...')
        embed.set_thumbnail(url=self.bot.user.display_avatar.with_static_format('png').url)
        embed.set_footer(text=ctx.author.name, icon_url=ctx.author.display_avatar.with_static_format('png').url)

        current_time = await asyncio.to_thread(datetime.utcnow)
        await ctx.respond(embed=embed, ephemeral=True)

        shard_ping = [_[1] for _ in self.bot.latencies]
        embed.description = f'API ping: `{round(sum(shard_ping) / len(shard_ping) * 1000)}ms`\nMessage Ping: `{round((await asyncio.to_thread(datetime.utcnow) - current_time).total_seconds() * 1000)}ms`'

        await ctx.edit(embed=embed)

    @slash_command(description="See Apple Releases's statistics.")
    async def stats(self, ctx: discord.ApplicationContext) -> None:
        start_time = datetime.fromtimestamp(self.bot.start_time)

        process = psutil.Process()
        embed = discord.Embed.from_dict({
            'title': 'Statistics',
            'fields': [{
                'name': 'Bot Started',
                'value': format_dt(start_time, style='R'),
                'inline': False
            },
            {
                'name': 'Python Version',
                'value': '.'.join(str(_) for _ in (sys.version_info.major, sys.version_info.minor, sys.version_info.micro)),
                'inline': False
            },
            {
                'name': 'CPU Usage',
                'value': f'{psutil.cpu_percent()}%',
                'inline': False
            },
            {
                'name': 'Memory Usage',
                'value': f'{floor(process.memory_info().rss/1000000)} MB',
                'inline': False
            }],
            'footer': {
                'text': ctx.author.display_name,
                'icon_url': str(ctx.author.display_avatar.with_static_format('png').url)
            }
        })

        await ctx.respond(embed=embed, ephemeral=True)


def setup(bot):
    bot.add_cog(MiscCog(bot))
