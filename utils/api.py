from datetime import datetime
from pytz import timezone as tz
from time import sleep
from utils.logger import logger

import aiohttp
import bs4
import discord
import feedparser
import json


VALID_RELEASES = (
    'iOS',
    'iPadOS',
    'macOS',
    'tvOS',
    'watchOS'
)

def format_feed(feed: list) -> list:
    """Formats recieved RSS entries into an interable JSON.
    
    Args:
        feed (list): List of RSS entries.
    Returns:
        JSON object
    """
    # Introduce needed variables
    releases = []
    # Iterate through items in feed
    for item in feed:
        if item.get('title').split()[0] in VALID_RELEASES:
            releases.append(item)
    # Return what we found
    return releases

async def fetch_firmwares() -> list:
    """Fetches all (recently) released firmwares.
    
    Returns:
        JSON object of recently released firmwares.
    """
    # Introduce needed variable
    releases = []
    # Fetch beta releases
    betas = format_feed(feedparser.parse('https://developer.apple.com/news/releases/rss/releases.rss').entries)
    if len(betas) > 0:
        releases.append(betas)
    # Fetch stable releases
    stable = format_feed(feedparser.parse('https://www.apple.com/newsroom/rss-feed.rss').entries)
    if len(stable) > 0:
        releases.append(stable)
    # Return what we found
    return releases

async def compare_firmwares(to_compare: list) -> list:
    """Compares already fetched firmware list to the current firmwares.
    
    Args:
        to_compare (dict): Dictionary object of firmwares.
    Returns:
        Firmwares in recent list that weren't in previous.
    """
    # Get all firmwares from the API
    firmwares = await fetch_firmwares()
    # Compare new firmwares to old firmwares
    differences = []
    for firmware in firmwares:
        # Check if the firmware is new
        if firmware not in to_compare:
            # Add the new firmware to the list of differences
            differences.append(firmware)
    # Return the differences
    return differences

async def format_ping(firm: dict, bot, guild: discord.Guild) -> str:
    """Formats the mention of the appropriate role for a release.
    
    Args:
        firm (dict): Firmware object.
        bot: Bot object.
        guild: Server guild object.
    Returns:
        Pre-formatted role mention.
    """
    async with bot.db.execute('SELECT data FROM roles WHERE guild = ?', (guild.id,)) as cursor:
        roles = json.loads((await cursor.fetchone())[0])
    for os in roles.keys():
        if os == firm.get('title').split()[0]:
            return '<@&{}>'.format(roles[os].get('role'))

async def get_icon(firm: dict) -> str:
    """Gets the icon for a release.
    
    Args:
        firm (dict): Firmware to fetch the icon for.
    Returns:
        Icon URL.
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(firm.get('link')) as response:
            soup = bs4.BeautifulSoup(await response.text(), features='html.parser')
            return soup.findAll(attrs={'property': 'og:image'})[0]['content']

def format_build_number(firm: dict) -> str: return firm.get('title').split('(')[1].split(' |')[0].replace(')', '')

def format_version(firm: dict) -> str: return firm.get('title').split(' (')[0]

def format_date(firm: dict) -> datetime: return tz('US/Pacific').localize(datetime.strptime(firm.get('published')[:-4], '%a, %d %b %Y %H:%M:%S'))