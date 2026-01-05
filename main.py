"""
Kyra Discord Bot - Main Entry Point
A modern, powerful Discord bot with 200+ commands across 15 categories.

Author: Natrix & Contributors
Version: 2.0.0 (Modernized)
"""
import os
import asyncio
import traceback

import aiohttp
import discord
from discord.ext import commands

from core import Context
from core.Olympus import Olympus
from utils.config import BOT_NAME, COMMAND_LOG_WEBHOOK, Colors, Emojis
from utils.database import DatabaseManager

import jishaku

# ============================================
# JISHAKU CONFIGURATION
# ============================================
os.environ["JISHAKU_NO_DM_TRACEBACK"] = "False"
os.environ["JISHAKU_HIDE"] = "True"
os.environ["JISHAKU_NO_UNDERSCORE"] = "True"
os.environ["JISHAKU_FORCE_PAGINATOR"] = "True"

# ============================================
# BOT INITIALIZATION
# ============================================
client = Olympus()
TOKEN = os.getenv("TOKEN")


# ============================================
# EVENT HANDLERS
# ============================================

@client.event
async def on_ready():
    """Called when the bot is ready and connected to Discord"""
    await client.wait_until_ready()
    
    # Initialize databases
    await DatabaseManager.initialize_databases()
    
    # ASCII Art Banner
    print("""
\033[1;35m
    ____   ___  _   _ _   _ 
   / ___| / _ \| \ | | | | |
   \___ \| | | |  \| | | | |
    ___) | |_| | |\  | |_| |
   |____/ \___/|_| \_| \___/ 
\033[0m
    """)
    
    print(f"✅ {BOT_NAME} is now online!")
    print(f"👤 Logged in as: {client.user}")
    print(f"🏰 Connected to: {len(client.guilds)} guilds")
    print(f"👥 Serving: {len(client.users)} users")
    print(f"🔧 Prefix: Use guild-specific prefix or mention")
    print("━" * 50)


@client.event
async def on_command_completion(context: commands.Context) -> None:
    """
    Log command executions to a webhook.
    This provides analytics on bot usage.
    """
    # Ignore specific test user
    if context.author.id == 1070619070468214824:
        return
    
    # Skip if no webhook configured
    if not COMMAND_LOG_WEBHOOK:
        return
    
    command_name = context.command.qualified_name.split("\n")[0]
    
    async with aiohttp.ClientSession() as session:
        webhook = discord.Webhook.from_url(COMMAND_LOG_WEBHOOK, session=session)
        
        try:
            embed = create_command_log_embed(context, command_name)
            await webhook.send(embed=embed)
        except Exception as e:
            print(f'❌ Failed to log command: {e}')
            traceback.print_exc()


def create_command_log_embed(context: commands.Context, command_name: str) -> discord.Embed:
    """Create a nicely formatted embed for command logging"""
    embed = discord.Embed(color=Colors.DEFAULT)
    
    avatar_url = context.author.display_avatar.url
    embed.set_author(
        name=f"Command: {command_name}",
        icon_url=avatar_url
    )
    embed.set_thumbnail(url=avatar_url)
    
    # Command information
    embed.add_field(
        name=f"{Emojis.STATS} Command",
        value=f"`{command_name}`",
        inline=False
    )
    
    # User information
    embed.add_field(
        name=f"{Emojis.INFO} Executed By",
        value=f"{context.author} | ID: [{context.author.id}](https://discord.com/users/{context.author.id})",
        inline=False
    )
    
    # Guild information (if in a guild)
    if context.guild:
        embed.add_field(
            name=f"{Emojis.SETTINGS} Server",
            value=f"{context.guild.name} | ID: {context.guild.id}",
            inline=False
        )
        embed.add_field(
            name=f"{Emojis.INFO} Channel",
            value=f"{context.channel.name} | ID: {context.channel.id}",
            inline=False
        )
    else:
        embed.add_field(
            name=f"{Emojis.INFO} Location",
            value="Direct Message",
            inline=False
        )
    
    embed.timestamp = discord.utils.utcnow()
    embed.set_footer(
        text=f"{BOT_NAME} Command Logs",
        icon_url=client.user.display_avatar.url
    )
    
    return embed


# ============================================
# MAIN EXECUTION
# ============================================

async def main():
    """Main bot startup routine"""
    async with client:
        # Clear the terminal for a clean startup
        os.system("clear")
        
        # Load jishaku extension for debugging
        await client.load_extension("jishaku")
        
        # Start the bot
        await client.start(TOKEN)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n\n👋 {BOT_NAME} is shutting down gracefully...")
    except Exception as e:
        print(f"\n\n❌ Fatal error occurred:")
        traceback.print_exc()
