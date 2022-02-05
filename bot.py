#!/usr/bin/env python3

# imports
from dotenv.main import load_dotenv
from utils.logger import logger

import aiohttp
import aiopath
import aiosqlite #TODO: Move to MongoDB
import asyncio
import discord
import os
import sys
import time

async def startup():
    if sys.version_info.major < 3 and sys.version_info.minor < 9:
        logger.error('Apple Releases requires Python 3.9 or higher. Exiting. (See \'https://phoenixnap.com/kb/upgrade-python\' for assistance)')
        exit(1)

    load_dotenv()
    if 'AR_TOKEN' not in os.environ.keys():
        logger.error('Bot token not set in \'AR_TOKEN\' environment variable. Exiting. (See \'.env\')')
        exit(1)

    mentions = discord.AllowedMentions(everyone=False, users=False, roles=True)
    bot = discord.AutoShardedBot(
        help_command=None,
        intents=discord.Intents.default(),
        allowed_mentions=mentions,
        activity=discord.Activity(type=discord.ActivityType.watching, name='for new releases')
    )

    bot.start_time = time.time()
    bot.load_extension('cogs.utils') # Load utils cog first
    cogs = aiopath.AsyncPath('cogs')
    async for cog in cogs.glob('*.py'):
        if cog.stem == 'utils':
            continue

        bot.load_extension(f'cogs.{cog.stem}')

    db_path = aiopath.AsyncPath('Data/bot.db')
    await db_path.parent.mkdir(exist_ok=True)
    async with aiosqlite.connect(db_path) as db, aiohttp.ClientSession() as session:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS roles(
            guild INTEGER,
            data JSON
            )
            ''')
        await db.commit()

        bot.db = db
        bot.session = session

        try:
            await bot.start(os.environ.get('AR_TOKEN'))
        except discord.LoginFailure:
            logger.error('Token invalid, make sure the \'AR_TOKEN\' environment variable is set to your bot token. Exiting. (See \'.env\')')
            exit(1)


if __name__ == '__main__':
    try:
        loop = asyncio.new_event_loop()
        loop.run_until_complete(startup())
        loop.close()
    except KeyboardInterrupt:
        exit(0)
