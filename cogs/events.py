from datetime import datetime
from discord.ext import commands, tasks
from discord.utils import format_dt
from utils import api, logger

import asyncio
import discord
import feedparser
import json


class EventsCog(discord.Cog, name='Events'):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

        self.utils = self.bot.get_cog('Utilities')
        self.firmwares = None
        self.release_checker.start()

    @tasks.loop()
    async def release_checker(self) -> None:
        await self.bot.wait_until_ready()

        print('checking for new releases')
        if self.firmwares is None:
            #self.firmwares = await api.fetch_firmwares()
            self.firmwares = api.format_feed(feedparser.parse('releases.rss').entries)
            return

        firm_diff = await api.compare_firmwares(self.firmwares) # Check for any new firmwares 
        if len(firm_diff) > 0:
            self.firmwares = await api.fetch_firmwares() # Replace cached firmwares with new ones

            for firm in firm_diff[0]:
                embed = {
                    'title': 'New Release',
                    'description': api.format_version(firm),
                    'timestamp': str(datetime.now()),
                    'color': int(discord.Color.blurple()),
                    'thumbnail': {
                        'url': await api.get_icon(firm)
                    },
                    'footer': {
                        'text': 'ReleaseBot • Made by m1sta and Jaidan',
                        'icon_url': str(self.bot.user.display_avatar.with_static_format('png').url)
                    },
                    'fields': [
                        {
                            'name': 'Release Date',
                            'value': format_dt(api.format_date(firm)),
                            'inline': False
                        },
                        {
                            'name': 'Build Number',
                            'value': api.format_build_number(firm),
                            'inline': False
                        },
                        {
                            'name': 'URL',
                            'value': f'[Click me!]({firm.get("link")})',
                            'inline': False
                        }
                    ]
                }

                async with self.bot.db.execute('SELECT * FROM roles') as cursor:
                    data = await cursor.fetchall()

                for item in data:
                    guild = self.bot.get_guild(item[0])

                    roles = json.loads(item[1])
                    channel = guild.get_channel(roles[api.format_version(firm).split()[0]].get('channel'))

                    await channel.send(content=await api.format_ping(firm, self.bot, guild), embed=discord.Embed.from_dict(embed))
        
        await asyncio.sleep(60)

    @discord.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild) -> None:
        await self.bot.wait_until_ready()

        if not guild.me.guild_permissions.manage_roles:
            embed = {
                'title': 'Hey!',
                'description': f"I need the 'Manage Roles' permission to function properly. Please kick & re-invite me using this link: {self.utils.invite}.",
                'color': int(discord.Color.red())
            }

            for channel in guild.text_channels:
                try:
                    await channel.send(embed=discord.Embed.from_dict(embed))
                    break
                except:
                    pass

        roles = dict()
        for os in ('tvOS', 'watchOS', 'iOS', 'iPadOS', 'macOS'):
            role = await guild.create_role(name=f'{os} Releases', reason='Created by ReleaseBot')
            roles[os] = {
                'role': role.id,
                'channel': 846383888862937183
            }

        await self.bot.db.execute('INSERT INTO roles(guild, data) VALUES(?,?)', (guild.id, json.dumps(roles)))
        await self.bot.db.commit()

    @discord.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild) -> None:
        await self.bot.wait_until_ready()

        async with self.bot.db.execute('SELECT data FROM roles WHERE guild = ?', (guild.id,)) as cursor:
            roles = json.loads((await cursor.fetchone())[0])

        for os in roles.keys():
            role = guild.get_role(roles[os].get('role'))
            if role is not None:
                await role.delete(reason='Deleted by ReleaseBot')

        await self.bot.db.execute('DELETE FROM roles WHERE guild = ?', (guild.id,))
        await self.bot.db.commit()

    @discord.Cog.listener()
    async def on_ready(self) -> None:
        print('Bot is now online.')

    @discord.Cog.listener()
    async def on_command_error(self, ctx: discord.ApplicationContext, error) -> None:
        await self.bot.wait_until_ready()
        if (isinstance(error, commands.errors.NotOwner)) or \
        (isinstance(error, discord.MissingPermissions)):
            pass

        else:
            raise error


def setup(bot):
    bot.add_cog(EventsCog(bot))
