from .api import VALID_RELEASES
from datetime import datetime
from pytz import timezone as tz

import aiohttp
import bs4
import discord
import json


def format_build_number(firm: dict) -> str: return firm.get('title').split('(')[1].split(' |')[0].replace(')', '')

def format_version(firm: dict) -> str: return firm.get('title').split(' (')[0]

def format_date(firm: dict) -> datetime: return tz('US/Pacific').localize(datetime.strptime(firm.get('pubdate')[:-4], '%a, %d %b %Y %H:%M:%S'))

class Release():
    def __init__(self, rss: dict):
        # Raw RSS
        self.__rss = rss
        # Firmware Type
        self.type: str = rss.get('title').split()[0] if rss.get('title').split()[0] in VALID_RELEASES else 'Other'
        # Firmware
        self.firmware: str = format_version(rss)
        # Build number
        self.build_number: str = format_build_number(rss)
        # Link
        self.link: str = rss.get('link')
        # Description
        self.description: str = rss.get('description')
        # Release date
        self.date: datetime = format_date(rss)

    async def get_icon(self) -> str:
        """Gets the icon for the release.
    
        Args:
            firm (dict): Firmware to fetch the icon for.
        Returns:
            Icon URL.
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(self.link) as resp:
                response = bs4.BeautifulSoup(await resp.text(), features='html.parser').findAll(attrs={'property': 'og:image'})[0]['content']
                resp.close()
                await session.close()
                return response

    async def ping(self, bot: discord.Bot, guild: discord.Guild):
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
