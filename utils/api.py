# imports
from .logger import logger
from .types import OtherRelease, Release, ComparedFirmwares
from aiopath import AsyncPath
from typing import Union

import aiofiles
import aiohttp
import bs4
import plistlib

VALID_RELEASES = (
    'iOS',
    'iPadOS',
    'macOS',
    'tvOS',
    'watchOS'
)

map = [
    {
        'name': 'AirTag Firmware',
        'xml': 'https://mesu.apple.com/assets/com_apple_MobileAsset_MobileAccessoryUpdate_DurianFirmware/com_apple_MobileAsset_MobileAccessoryUpdate_DurianFirmware.xml',
        'img': 'https://www.att.com/catalog/en/idse/Apple/Apple%20AirTag/White%20_1%20Pack_-hero-zoom.png'
    },
    {
        'name': 'audioOS',
        'xml': 'https://mesu.apple.com/assets/audio/com_apple_MobileAsset_SoftwareUpdate/com_apple_MobileAsset_SoftwareUpdate.xml',
        'img': 'https://help.apple.com/assets/61608C271E13E80A1C5310CE/61608C291E13E80A1C5310D8/en_US/03d850c212af22000d02c97705cf6704.png'
    },
    {
        'name': 'AirPods 1 and 2 Firmware',
        'xml': 'https://mesu.apple.com/assets/com_apple_MobileAsset_MobileAccessoryUpdate_A2032_EA/com_apple_MobileAsset_MobileAccessoryUpdate_A2032_EA.xml',
        'img': 'https://www.freepnglogos.com/uploads/airpods-png/airpods-wireless-headphones-apple-indiaistore-4.png'
    },
    {
        'name': 'AirPods Pro Firmware',
        'xml': 'https://mesu.apple.com/assets/com_apple_MobileAsset_MobileAccessoryUpdate_A2084_EA/com_apple_MobileAsset_MobileAccessoryUpdate_A2084_EA.xml',
        'img': 'https://images.macrumors.com/t/iIHGbqwaHJgcnjYzsy1-BHQsz7Y=/1600x/article-new/2020/04/AirPods-PRo-isolated.png'
    },
    {
        'name': 'AirPods 3 Firmware',
        'xml': 'https://mesu.apple.com/assets/com_apple_MobileAsset_MobileAccessoryUpdate_A2564_EA/com_apple_MobileAsset_MobileAccessoryUpdate_A2564_EA.xml',
        'img': 'https://www.att.com/catalog/en/idse/Apple/Apple%20AirPods%20_3rd%20generation_/White-hero-zoom.png'
    }
]

async def rss(url: str):
    if await AsyncPath(url).is_file():
        async with aiofiles.open(url) as f:
            r = await f.read()

    else:
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

async def xml(obj: dict):
    try:
        async with aiohttp.ClientSession() as session, session.get(obj.get('xml')) as resp:
            try:
                plist = plistlib.loads(await resp.read())
            except Exception:
                logger.error('Could not parse the XMML: ', obj.get('xml'))
 
    except Exception:
        logger.error('[XML] Error fetching the URL: ', obj.get('xml'))

    for _ in plist['Assets']:
        if _['Build'] is None is None or _['__BaseURL'] is None:
            pass
        else:
            return {
                'version': _['Build'],
                'zip': _['__BaseURL'] + _['__RelativePath'],
                'orig': obj
            }
    
    return

def format_feed(feed: list) -> list[Release]:
    """Formats recieved RSS entries into an interable list of Release objects.
    
    Args:
        feed (list): List of RSS entries.
    Returns:
        
    """

    # Return what we found
    return [Release(item) for item in feed]

def format_feed_xml(feed: dict) -> list[OtherRelease]:
    """Formats recieved XML entry into an OtherRelease object.
    
    Args:
        feed (list): XML entry.
    Returns:
        
    """

    # Return what we found
    return OtherRelease(feed)

async def fetch_releases() -> list[Union[Release, OtherRelease]]:
    """Fetches all (recent) Apple releases.
    
    Returns:
        List of recent Apple releases.
    """
    # Add normal releases
    releases: list[Union[Release, OtherRelease]] = format_feed(await rss('https://developer.apple.com/news/releases/rss/releases.rss'))
    # Add other releases
    for item in map:
        releases.append(format_feed_xml(await xml(item)))
    return releases

async def compare_releases(to_compare: list[Union[Release, OtherRelease]]) -> ComparedFirmwares:
    """Compares already fetched release list to the current releases.
    
    Args:
        to_compare (dict): Dictionary object of releases.
    Returns:
        Releases in recent list that weren't in previous.
    """
    # Get all releases from the API
    releases = await fetch_releases()
    # Initialize array for differences
    differences = []
    
    for release in releases:
        if release not in to_compare:
            differences.append(release)

    # Compare the old & new release lists
    return ComparedFirmwares(differences, releases)
