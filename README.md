<img src="./img/logo.png" alt="Apple Releases Logo" title="Apple Releases" align="right" height="60"/>

# Apple Releases

[![License](https://img.shields.io/github/license/m1stadev/AppleReleases)](https://github.com/m1stadev/AppleReleases/blob/master/LICENSE)
[![Stars](https://img.shields.io/github/stars/m1stadev/AppleReleases)](https://github.com/m1stadev/AppleReleases/stargazers)
[![LoC](https://img.shields.io/tokei/lines/github/m1stadev/AppleReleases)](https://github.com/m1stadev/AppleReleases)
[![Discord Invite](https://img.shields.io/badge/Discord-Invite%20AppleReleases-%237289DA)](https://m1sta.xyz/applereleases)

Get notifications in your Discord server of any software releases from [Apple](https://developer.apple.com/news/releases/).  
Created with love by myself and [Jaidan](https://github.com/ja1dan).

## Running
To locally host your own instance, [create a Discord bot](https://discord.com/developers) and follow these steps...

1. Clone this repository

2. Create a virtual env and install dependencies

        python3 -m venv --upgrade-deps env
        source env/bin/activate
        pip3 install -Ur requirements.txt

3. Create a `.env` file containing `AR_TOKEN=<TOKEN>`, replacing `<TOKEN>` with your bot token.

4. Start your instance

        python3 bot.py

## Support
For any questions/issues you have, join my [Discord](https://m1sta.xyz/discord).
