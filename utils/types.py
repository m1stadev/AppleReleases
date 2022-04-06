# imports
from . import api
from datetime import datetime
from pytz import timezone as tz
from typing import Optional, List, Union

import aiohttp
import bs4
import discord
import json

class OtherRelease():
    def __init__(self, dict: dict):
        # build number
        self.build: str = dict.get('version')
        # type
        self.type: str = 'Other'
        # release zip
        self.zip: str = dict.get('zip')
        # name
        self.name: str = dict.get('orig').get('name')
        # xml
        self.xml: str = dict.get('orig').get('xml')
        # image
        self.img: str = dict.get('orig').get('img')
        # version
        self.version: str = f'{self.name} {self.build}'
    
    async def ping(self, bot: discord.Bot, guild: discord.Guild) -> Optional[str]:
        """Formats the mention of the appropriate role for a release.
    
        Args:
            bot (discord.Bot): Bot object.
            guild (discord.Guild): Server guild object.
        Returns:
            Pre-formatted role mention.
        """
        async with bot.db.execute('SELECT data FROM roles WHERE guild = ?', (guild.id,)) as cursor:
            roles = json.loads((await cursor.fetchone())[0])

        return guild.get_role(roles['Other'].get('role')).mention

class Release():
    def __init__(self, rss: dict):
        # Raw RSS
        self._rss = rss
        # Release Type
        self.type: str = rss.get('title').split()[0] if rss.get('title').split()[0] in api.VALID_RELEASES else 'Other'
        # Version
        self.version: str = self.__format_version()
        # Build number
        self.build_number: Optional[str] = self.__format_build_number() if rss.get('title').split()[0] in api.VALID_RELEASES else None
        # Link
        self.link: str = rss.get('link')
        # Description
        self.description: str = rss.get('description')
        # Release date
        self.date: datetime = self.__format_date()

    def __format_build_number(self) -> str: return self._rss.get('title').split('(')[1].split(')')[0].replace(' | ', '')

    def __format_version(self) -> str: return self._rss.get('title').split(' (')[0]

    def __format_date(self) -> datetime: return tz('US/Pacific').localize(datetime.strptime(self._rss.get('pubdate')[:-4], '%a, %d %b %Y %H:%M:%S'))

    async def get_icon(self) -> str:
        """Gets the icon for the release.
    
        Returns:
            Icon URL.
        """
        try:
            return getattr(self, '__icon')
        except AttributeError:
            pass

        async with aiohttp.ClientSession() as session, session.get(self.link) as resp:
            self.__icon = bs4.BeautifulSoup(await resp.text(), features='html.parser').findAll(attrs={'property': 'og:image'})[0]['content']
            return self.__icon

    async def ping(self, bot: discord.Bot, guild: discord.Guild) -> Optional[str]:
        """Formats the mention of the appropriate role for a release.
    
        Args:
            bot (discord.Bot): Bot object.
            guild (discord.Guild): Server guild object.
        Returns:
            Pre-formatted role mention.
        """
        async with bot.db.execute('SELECT data FROM roles WHERE guild = ?', (guild.id,)) as cursor:
            roles = json.loads((await cursor.fetchone())[0])

        for os in roles.keys():
            if os == self.type:
                return guild.get_role(roles[os].get('role')).mention

class ComparedFirmwares():
    def __init__(self, diff, fetched):
        # Firmware differences
        self.differences: List[Union[Release, OtherRelease]] = diff
        # Fetched firmwares
        self.firmwares: List[Union[Release, OtherRelease]] = fetched