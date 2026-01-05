"""
Kyra Bot - Core Bot Class
Modern implementation of the Discord bot with optimized prefix handling.
"""
from __future__ import annotations
from discord.ext import commands
import discord
import aiohttp
import typing
from typing import List, Optional
import aiosqlite
from colorama import Fore, Style, init

from utils.config import OWNER_IDS, DEFAULT_PREFIX
from utils import getConfig
from utils.database import DatabaseManager
from .Context import Context

init(autoreset=True)

# Extensions to load on startup
extensions: List[str] = ["cogs"]


class Olympus(commands.AutoShardedBot):
    """
    Main bot class - extends AutoShardedBot for scalability.
    Handles prefix management, command processing, and event handling.
    """

    def __init__(self, *args, **kwargs):
        # Configure intents - full permissions for all events
        intents = discord.Intents.all()
        intents.presences = True
        intents.members = True
        
        super().__init__(
            command_prefix=self.get_prefix,
            case_insensitive=True,
            intents=intents,
            status=discord.Status.do_not_disturb,
            strip_after_prefix=True,
            owner_ids=OWNER_IDS,
            allowed_mentions=discord.AllowedMentions(
                everyone=False,
                replied_user=False,
                roles=False
            ),
            shard_count=2
        )

    async def setup_hook(self):
        """Called when the bot is setting up - loads all extensions"""
        await self.load_extensions()

    async def load_extensions(self):
        """Load all bot extensions (cogs)"""
        print(Fore.CYAN + Style.BRIGHT + "\n🔧 Loading Extensions...")
        
        for extension in extensions:
            try:
                await self.load_extension(extension)
                print(Fore.GREEN + Style.BRIGHT + f"  ✅ Loaded: {extension}")
            except Exception as e:
                print(Fore.RED + Style.BRIGHT + f"  ❌ Failed to load {extension}: {e}")
        
        print(Fore.CYAN + Style.BRIGHT + "━" * 50 + "\n")

    async def on_connect(self):
        """Called when bot connects to Discord"""
        await self.change_presence(
            status=discord.Status.do_not_disturb,
            activity=discord.Activity(
                type=discord.ActivityType.playing,
                name='Avec KTX✨ Family'
            )
        )

    async def get_prefix(self, message: discord.Message):
        """
        Dynamic prefix handler.
        - Supports guild-specific prefixes
        - Supports no-prefix users
        - Always allows mention as prefix
        """
        if message.guild:
            # In guild - check for no-prefix users
            is_np = await DatabaseManager.is_np_user(message.author.id)
            
            # Get guild's custom prefix
            data = await getConfig(message.guild.id)
            prefix = data.get("prefix", DEFAULT_PREFIX)
            
            if is_np:
                # No-prefix user - allow both prefix and no prefix
                return commands.when_mentioned_or(prefix, '')(self, message)
            else:
                # Regular user - require prefix or mention
                return commands.when_mentioned_or(prefix)(self, message)
        else:
            # In DMs - check for no-prefix users
            is_np = await DatabaseManager.is_np_user(message.author.id)
            
            if is_np:
                # No-prefix user in DMs
                return commands.when_mentioned_or('$', '')(self, message)
            else:
                # Regular user in DMs - only mention
                return commands.when_mentioned_or('')(self, message)

    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        """
        Handle edited messages - re-process commands if content changed.
        This allows users to edit their messages and have commands re-executed.
        """
        # Skip if content didn't change
        if before.content == after.content:
            return
        
        # Skip DMs and bot messages
        if after.guild is None or after.author.bot:
            return
        
        # Get context and check if it's a command
        ctx: Context = await self.get_context(after, cls=Context)
        if ctx.command is None:
            return
        
        # Skip if in thread (avoid issues)
        if isinstance(ctx.channel, discord.Thread):
            return
        
        # Re-invoke the command
        await self.invoke(ctx)

    async def send_raw(
        self,
        channel_id: int,
        content: str,
        **kwargs
    ) -> Optional[discord.Message]:
        """Send a raw message using the HTTP API"""
        return await self.http.send_message(channel_id, content, **kwargs)

    async def invoke_help_command(self, ctx: Context) -> None:
        """Invoke the help command for a given context"""
        return await ctx.send_help(ctx.command)

    async def fetch_message_by_channel(
        self,
        channel: discord.TextChannel,
        message_id: int
    ) -> Optional[discord.Message]:
        """
        Fetch a specific message from a channel by ID.
        More efficient than searching through entire history.
        """
        async for msg in channel.history(
            limit=1,
            before=discord.Object(message_id + 1),
            after=discord.Object(message_id - 1),
        ):
            return msg
        return None


def setup_bot() -> Olympus:
    """
    Factory function to create a bot instance.
    Can be used for testing or alternative initialization.
    """
    intents = discord.Intents.all()
    bot = Olympus(intents=intents)
    return bot
