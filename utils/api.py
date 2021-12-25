import aiohttp
from time import sleep
from utils.logger import logger

async def fetch_firmwares() -> list:
    # Initialize an AiOHTTP session
    async with aiohttp.ClientSession() as session:
        # Get all firmwares from the API
        async with session.get('https://api.ipsw.me/v4/releases') as response:
            resp = await response.json()
            releases = []
            # Format the releases
            for obj in resp:
                for release in obj.get('releases'):
                    releases.append(release)
            return releases

async def compare_firmwares(to_compare: dict) -> list:
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

async def start_loop():
    # Get all firmwares from the API
    firmwares = await fetch_firmwares()
    # While the bot is running,
    while True:
        # Compare the differences in firmwares from the API,
        differences = await compare_firmwares(firmwares)
        # And if there are differences,
        if len(differences) > 0:
            # Log them out.
            for diff in differences:
                logger.info(f'DIFFERENCE DETECTED! {diff.get("name")} (Released for {diff.get("count")} devices on {diff.get("date")})')
        # Replace the old firmwares with the new ones
        firmwares = await fetch_firmwares()
        # And sleep for 10 minutes.
        sleep(600)