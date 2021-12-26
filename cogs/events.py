from datetime import datetime
from discord.ext import commands, tasks
from discord.utils import format_dt
from typing import List
from utils import api, types
from pytz import timezone as tz
from views.buttons import SelectView

import asyncio
import discord
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

        if self.firmwares is None:
            #self.firmwares = await api.fetch_firmwares()
            self.firmwares: List[types.Release] = api.format_feed(await api.rss('/Users/jaidan/Developer/release-bot/releases.rss'))
            return

        firm_diff: List[types.Release] = await api.compare_firmwares(self.firmwares) # Check for any new firmwares 
        if len(firm_diff) > 0:
            self.firmwares: List[types.Release] = await api.fetch_firmwares() # Replace cached firmwares with new ones

            for firm in firm_diff:
                embed = {
                    'title': 'New Release',
                    'description': firm.firmware,
                    'timestamp': str(tz('US/Pacific').localize(datetime.now())),
                    'color': int(discord.Color.blurple()),
                    'thumbnail': {
                        'url': await firm.get_icon()
                    },
                    'fields': [
                        {
                            'name': 'Release Date',
                            'value': format_dt(firm.date),
                            'inline': False
                        },
                        {
                            'name': 'Build Number',
                            'value': firm.build_number,
                            'inline': False
                        }
                    ],
                    'footer': {
                        'text': 'Apple Releases • Made by m1sta and Jaidan',
                        'icon_url': str(self.bot.user.display_avatar.with_static_format('png').url)
                    }
                }

                buttons = [{
                    'label': 'Link',
                    'style': discord.ButtonStyle.link,
                    'url': firm.link
                }]

                async with self.bot.db.execute('SELECT * FROM roles') as cursor:
                    data = await cursor.fetchall()

                for item in data:
                    os = firm.type
                    guild = self.bot.get_guild(item[0])

                    roles = json.loads(item[1])
                    if not roles[os].get('enabled'):
                        continue

                    channel = guild.get_channel(roles[os].get('channel'))
                    await channel.send(content=await firm.ping(self.bot, guild), embed=discord.Embed.from_dict(embed), view=SelectView(buttons, context=None, public=True, timeout=None))
        
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
        for os in api.VALID_RELEASES:
            try:
                role = next(_ for _ in guild.roles if _.name == f'{os} Releases')
            except StopIteration:
                role = await guild.create_role(name=f'{os} Releases', reason='Created by Apple Releases')

            roles[os] = {
                'role': role.id,
                'channel': 924507072194830376,
                'enabled': True
            }

        try:
            role = next(_ for _ in guild.roles if _.name == 'Other Apple Releases')
        except StopIteration:
            role = await guild.create_role(name='Other Apple Releases', reason='Created by Apple Releases')

        roles['Other'] = {
            'role': role.id,
            'channel': 924507072194830376,
            'enabled': True
        }

        await self.bot.db.execute('INSERT INTO roles(guild, data) VALUES(?,?)', (guild.id, json.dumps(roles)))
        await self.bot.db.commit()

    @discord.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild) -> None:
        await self.bot.wait_until_ready()

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
