from .logger import logger
from .types import Release

import aiohttp
import bs4


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
        logger.error('Error fetching the URL: ', url)

    try:    
        soup = bs4.BeautifulSoup(r, features='html.parser')
    except Exception:
        logger.error('Could not parse the xml: ', url)

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

def format_feed(feed: list) -> list:
    """Formats recieved RSS entries into an interable list of Release objects.
    
    Args:
        feed (list): List of RSS entries.
    Returns:
        
    """

    # Return what we found
    return [Release(item) for item in feed]

async def fetch_releases() -> list:
    """Fetches all (recent) Apple releases.
    
    Returns:
        List of recent Apple releases.
    """
    # Return releases
    return format_feed(await rss('https://developer.apple.com/news/releases/rss/releases.rss'))

async def compare_releases(to_compare: list) -> list:
    """Compares already fetched release list to the current releases.
    
    Args:
        to_compare (dict): Dictionary object of releases.
    Returns:
        Releases in recent list that weren't in previous.
    """
    # Get all releases from the API
    releases = await fetch_releases()

    # Compare the old & new release lists
    return [_ for _ in releases if _ not in to_compare]
