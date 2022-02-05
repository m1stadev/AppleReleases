# imports
from dotenv.main import load_dotenv

import argparse
import logging
import os
import radium as r

load_dotenv()

class Logger:
    def __init__(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--disable-discord-logs', help='Disables Discord logging.', action='store_true')
        parser.add_argument('--disable-webhook-logging', help='Disables logging to the webhook.', action='store_true')

        args = parser.parse_args()

        if not args.disable_discord_logs:
            discord_logger = logging.getLogger('discord')
            discord_logger.setLevel(logging.WARN)
            discord_logger.addHandler(r.Radium)
        self.logger = logging.Logger(__name__)
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(r.Radium)

        if os.environ.get("LOGGING_WEBHOOK_URL") is not None:
            if args.disable_webhook_logging:
                self.logger.info("Discord webhook logging is DISABLED!")
            else:
                owners = os.environ.get('OWNERS')
                l = list()
                if owners.split(',') is not None and owners.split('[') is not None:
                    for x in owners.split(','):
                        l.append(x.replace('[', '').replace(']', '').replace('"', '').replace('\'', '').replace(' ', ''))
                else:
                    l = [os.environ.get('OWNERS')]
                self.logger.info("Discord webhook logging is ENABLED!")
                wh = r.WebhookLogger(url=os.environ.get("LOGGING_WEBHOOK_URL"), ids_to_ping=l)
                discord_logger.addHandler(wh)
                self.logger.addHandler(wh)
        else:
            self.logger.info("Discord webhook logging is DISABLED!")

logger = Logger().logger
