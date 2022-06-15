import logging

import discord

log = logging.getLogger(__name__)

intents = discord.Intents.all()
client = discord.Client(intents=intents)