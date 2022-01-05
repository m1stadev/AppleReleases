from .logger import logger
from .types import AudioRelease, Release, ComparedFirmwares

import aiohttp
import bs4
import io
import plistlib


VALID_RELEASES = (
    'iOS',
    'iPadOS',
    'macOS',
    'tvOS',
    'watchOS'
)

async def rss(url: str):
    try:
        async with aiohttp.ClientSession() as session, session.get(url) as resp:
            r = await resp.text()

    except Exception:
        logger.error('[RSS] Error fetching the URL: ', url)

    try:    
        soup = bs4.BeautifulSoup(r, features='html.parser')
    except Exception:
        logger.error('Could not parse the RSS: ', url)

    articles = [
            {
                'title': a.find('title').text,
                'link': a.link.next_sibling.replace('\n','').replace('\t',''),
                'description': a.find('description').text,
                'pubdate': a.find('pubdate').text
            }
        for a in soup.findAll('item')
    ]

    return articles

async def plist(url: str):
    try:
        async with aiohttp.ClientSession() as session, session.get(url) as resp:
            r = io.BytesIO(await resp.read())

    except Exception:
        logger.error('[PLIST] Error fetching the URL: ', url)
    
    try:
        plist = plistlib.load(r)
    except Exception as e:
        logger.error('Could not parse the plist: ', url)
        print(e)

    a = plist['Assets'][0]
    articles = [
        {
            'version': a['Build']
        }
    ]
    
    return articles

def format_feed(feed: list) -> list:
    """Formats recieved RSS entries into an interable list of Release objects.
    
    Args:
        feed (list): List of RSS entries.
    Returns:
        
    """

    # Return what we found
    return [Release(item) for item in feed]

def format_feed_plist(feed: list, type: str) -> list:
    """Formats recieved plist entries into an interable list of AudioRelease objects.
    
    Args:
        feed (list): List of plist entries.
    Returns:
        
    """

    # Return what we found
    return [AudioRelease(item, type) for item in feed]

async def fetch_releases() -> list[Release | AudioRelease]:
    """Fetches all (recent) Apple releases.
    
    Returns:
        List of recent Apple releases.
    """
    # Add normal releases
    releases: list[Release] = format_feed(await rss('https://developer.apple.com/news/releases/rss/releases.rss'))
    return releases

async def compare_releases(to_compare: list[Release]) -> ComparedFirmwares:
    """Compares already fetched release list to the current releases.
    
    Args:
        to_compare (dict): Dictionary object of releases.
    Returns:
        Releases in recent list that weren't in previous.
    """
    # Get all releases from the API
    releases = await fetch_releases()

    # Compare the old & new release lists
    return ComparedFirmwares([r for r in releases if not any(r._rss == _._rss  for _ in to_compare)], releases)
