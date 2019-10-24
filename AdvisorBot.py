from discord.ext import commands
from utils import config

import discord
import datetime
import sys
import traceback


description = "Realm Grinder Advisor Bot written in Python by Alright#2304. Uses . prefix, mentioning the bot will also work."

extensions = ['cogs.notawiki']

def getPrefix(bot, msg):
    prefixes = ["."]
    return commands.when_mentioned_or(*prefixes)(bot, msg)

class AdvisorBot(commands.AutoShardedBot):
    def __init__(self):
        super().__init__(command_prefix=getPrefix, description=description, help_attrs=dict(hidden=True))

        for extension in extensions:
            try:
                self.load_extension(extension)
            except Exception:
                print(f'Failed to load extension {extension}.', file=sys.stderr)
                traceback.print_exc()

    async def on_ready(self):
        if not hasattr(self, 'uptime'):
            self.uptime = datetime.datetime.utcnow()
        await self.change_presence(status=discord.Status.online, activity=discord.Game('Helping grinders grind more'))

        print(f'Online and running. {self.user} (ID: {self.user.id})')

    def run(self):
        super().run(config.get_token(), reconnect=True)


if __name__ == '__main__':
    bot = AdvisorBot()
    bot.run()