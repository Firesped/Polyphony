import asyncio
import logging
import re

import discord
import discord.ext
import requests

from polyphony.helpers.decode_token import decode_token
from polyphony.settings import (
    TOKEN, EMOTE_CACHE_MAX, GUILD_ID,
)

log = logging.getLogger(__name__)


class HelperInstance(discord.Client):
    def __init__(
        self,
        **options,
    ):
        super().__init__(**options)
        self.lock = asyncio.Lock()
        self.invisible = False
        log.debug(f"Helper initialized")

    async def on_ready(self):
        """Execute on bot initialization with the Discord API."""
        log.debug(f"Helper started as {self.user}")

    async def edit_as(self, message: discord.Message, content, token, files=None):
        await self.wait_until_ready()
        msg = await self.get_channel(message.channel.id).fetch_message(message.id)
        if msg is None:
            log.debug("Helper failed to edit")
            return False
        async with self.lock:
            self.http.token = token
            await msg.edit(content=content, files=files)
            self.http.token = TOKEN
        if not self.invisible:
            await self.change_presence(status=discord.Status.invisible)
        return True

    async def send_as(
        self, message: discord.Message, content, token, files=None, reference=None, emote_cache=None
    ):
        await self.wait_until_ready()
        chan = self.get_channel(message.channel.id)
        if chan is None:
            log.debug("Helper failed to send")
            return False
        async with self.lock:
            self.http.token = token
            await chan.trigger_typing()

            # TODO: remove excessive emote_cache logging after feature is thoroughly production tested

            async def emote_cache_helper(ch_emote):
                try:
                    emote_name = re.findall(r':.+?:', ch_emote)[0][1:-1]
                    emote_id = re.findall(r':\d+>', ch_emote)[0][1:-1]
                    log.debug(f'Checking if {emote_id} (:{emote_name}:) is accessible without cache.')
                    if self.get_emoji(emote_id):
                        log.debug(log.debug(f'{emote_id} (:{emote_name}:) is accessible. Skipping...'))
                        return
                    log.debug(f'Getting emote image {emote_id} (:{emote_name}:)')
                    emote_image = requests.get(f'https://cdn.discordapp.com/emojis/{emote_id}.webp').content
                    log.debug(f'Uploading emote {emote_id} (:{emote_name}:)')
                    cached_emote = await emote_cache.create_custom_emoji(name=emote_name,
                                                                         image=emote_image)
                    log.debug(f'{emote_id} (:{emote_name}:) uploaded')
                    return ch_emote, f'<:{cached_emote.name}:{cached_emote.id}>', cached_emote
                except discord.Forbidden:
                    log.debug('Polyphony does not have permission to upload emote cache emoji')
                    return
                except discord.HTTPException as e:
                    log.debug(f'Failed to upload emote cache emoji\n{e}')
                    return

            # Emote cache
            if emote_cache:
                # TODO: Potentially allow user to turn emote cache on and off
                log.debug('Emote cache start')
                emotes = [*set(re.findall(r'<a?:.+?:\d+>', content))]  # Remove duplicates
                task_list = []
                for emote in emotes[0:EMOTE_CACHE_MAX]:
                    task_list.append(emote_cache_helper(emote))

                log.debug('Processing emote cache...')
                new_emotes = await asyncio.gather(*task_list)

                for emote in new_emotes:
                    if emote:
                        content = content.replace(emote[0], emote[1])

                log.debug(f'Message after emote cache => {content}')

            await chan.send(content=content, files=files, reference=reference)

            if emote_cache:
                # Delete emote cache after send
                log.debug('Deleting cached emotes after message send')
                delete_list = []
                for emote in new_emotes:
                    if emote:
                        delete_list.append(emote[2].delete())
                await asyncio.gather(*delete_list)
                log.debug('Emote cache complete')

            self.http.token = TOKEN
        if not self.invisible:
            await self.change_presence(status=discord.Status.invisible)
        return True
