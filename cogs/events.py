# imports
from discord.errors import Forbidden
from discord.ext import commands, tasks
from discord.utils import format_dt
from typing import List, Union
from utils import api, types, logger
from views.buttons import ReactionRoleButton, SelectView

import asyncio
import discord
import json

l = logger.logger

class EventsCog(discord.Cog, name='Events'):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

        self.utils = self.bot.get_cog('Utilities')
        self.releases = None
        self.release_checker.start()
    
    async def send_msgs(self, embed: dict, release: Union[types.Release, types.OtherRelease], data: dict) -> None:
        messaged_guilds = list()

        for item in data:
            if item[0] in messaged_guilds:
                continue

            roles = json.loads(item[1])
            guild = self.bot.get_guild(item[0])

            if guild is None: # Bot isn't in guild anymore
                l.warning(f'No longer in guild with id: {item[0]}, removing from database.')
                await self.bot.db.execute('DELETE FROM roles WHERE guild = ?', (item[0],))
                await self.bot.db.commit()

                continue

            os = release.type
            if not roles[os].get('enabled') or roles[os].get('channel') is None:
                continue

            channel = guild.get_channel(roles[os].get('channel')) # Channel is deleted/Bot doesn't have access to channel
            if channel is None:
                l.warning(f"Channel with id: {roles[os].get('channel')} is no longer accessible in guild: {guild.id}, disabling {os} releases for guild.")

                roles[os]['enabled'] = False
                await self.bot.db.execute('UPDATE roles SET data = ? WHERE guild = ?', (json.dumps(roles), guild.id))
                await self.bot.db.commit()

                continue

            try:
                if os in api.VALID_RELEASES:
                    button = [{
                        'label': 'Link',
                        'style': discord.ButtonStyle.link,
                        'url': release.link
                    }]
                    await channel.send(content=await release.ping(self.bot, guild), embed=discord.Embed.from_dict(embed), view=SelectView(button, context=None, public=True, timeout=None))
                else:
                    await channel.send(content=await release.ping(self.bot, guild), embed=discord.Embed.from_dict(embed))
                l.info(f'Sent {release.version} ({release.build_number}) release to guild: {guild.name}, channel: #{channel.name}.')
            except Forbidden:
                l.warning(f'Unable to send {os} releases to channel: #{channel.name} in guild: {guild.name}, disabling {os} releases for guild.')

                roles[os]['enabled'] = False
                await self.bot.db.execute('UPDATE roles SET data = ? WHERE guild = ?', (json.dumps(roles), guild.id))
                await self.bot.db.commit()

            except Exception as e:
                l.error(f'Failed to send {release.version} ({release.build_number}) release to channel: #{channel.name} in guild: {guild.name} with error: {e}')

            messaged_guilds.append(guild.id)
            await asyncio.sleep(1)

    @tasks.loop()
    async def release_checker(self) -> None:
        await self.bot.wait_until_ready()

        if self.releases is None:
            l.info('Populating release cache...')
            self.releases = await api.fetch_releases()
            l.info('Release cache populated, sleeping.')
            await asyncio.sleep(120)
            return

        firmwares: types.ComparedFirmwares = await api.compare_releases(self.releases) # Check for any new firmwares
        diff: List[Union[types.Release, types.OtherRelease]] = firmwares.differences
        if len(diff) > 0:
            l.info(f"{len(diff)} new release{'s' if len(diff) > 1 else ''} detected!")
            self.releases: List[Union[types.Release, types.OtherRelease]] = firmwares.firmwares # Replace cached firmwares with new ones

            for release in diff:
                embed = {
                    'title': 'New Release',
                    'description': release.version,
                    'color': int(discord.Color.blurple()),
                    'thumbnail': {
                        'url': await release.get_icon()
                    },
                    'fields': [],
                    'footer': {
                        'text': 'Apple Releases • Made by m1sta and Jaidan',
                        'icon_url': str(self.bot.user.display_avatar.with_static_format('png').url)
                    }
                }

                if release.type in api.VALID_RELEASES:
                    embed['fields'].append({
                            'name': 'Release Date',
                            'value': format_dt(release.date),
                            'inline': False
                        },{
                            'name': 'Build Number',
                            'value': release.build_number,
                            'inline': False
                        })

                async with self.bot.db.execute('SELECT * FROM roles') as cursor:
                    data = await cursor.fetchall()
                    
                await self.send_msgs(embed, release, data)

            l.info('Finished sending new releases.')

        await asyncio.sleep(120)

    @discord.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild) -> None:
        await self.bot.wait_until_ready()

        embed = {
            'title': 'Hello!',
            'description': 'In order to start using Apple Releases, please follow the instructions below:',
            'color': int(discord.Color.blurple()),
            'thumbnail': {
                'url': 'https://www.apple.com/ac/structured-data/images/open_graph_logo.png'
            },
            'fields': [
                {
                    'name': 'Setup',
                    'value': 'Run `/config setchannel` to specify a channel that you\'d like to announce Apple releases in.'
                },
                {
                    'name': 'Notification Roles',
                    'value': 'Run `/reactionrole` to send a message that will allow users to assign themselves notification roles.'
                },
                {
                    'name': 'What else can I do?',
                    'value': 'In order to see a complete list of my commands, run `/help`.'
                }
            ],
            'footer': {
                'text': 'Apple Releases • Made by m1sta and Jaidan',
                'icon_url': str(self.bot.user.display_avatar.with_static_format('png').url)
            }
        }
        for channel in guild.text_channels:
            try:
                await channel.send(embed=discord.Embed.from_dict(embed))
                break
            except:
                pass

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
                'channel': None,
                'enabled': True
            }

        try:
            role = next(_ for _ in guild.roles if _.name == 'Other Apple Releases')
        except StopIteration:
            role = await guild.create_role(name='Other Apple Releases', reason='Created by Apple Releases')

        roles['Other'] = {
            'role': role.id,
            'channel': None,
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
        for guild in self.bot.guilds:
            async with self.bot.db.execute('SELECT data FROM roles WHERE guild = ?', (guild.id,)) as cursor:
                data = json.loads((await cursor.fetchone())[0])

            view = discord.ui.View(timeout=None)

            roles = [guild.get_role(data[_]['role']) for _ in data.keys()]
            for role in roles:
                view.add_item(ReactionRoleButton(role, row=0 if roles.index(role) < 3 else 1))

            self.bot.add_view(view)

        l.info('Apple Releases is READY!')
        l.info(f'Logged in as {self.bot.user}. Serving {len(self.bot.guilds)} guild(s).')

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
