"""
Modernized Cog Loader for Kyra Discord Bot
Automatically loads all cogs without manual registration.
"""
from __future__ import annotations
from core import Olympus
from colorama import Fore, Style, init

# Commands
from .commands.help import Help
from .commands.general import General
from .commands.automod import Automod
from .commands.welcome import Welcomer
from .commands.fun import Fun
from .commands.Games import Games
from .commands.extra import Extra
from .commands.owner import Owner
from .commands.voice import Voice
from .commands.afk import afk
from .commands.ignore import Ignore
from .commands.Media import Media
from .commands.Invc import Invcrole
from .commands.giveaway import Giveaway
from .commands.Embed import Embed
from .commands.steal import Steal
from .commands.ship import Ship
from .commands.timer import Timer
from .commands.blacklist import Blacklist
from .commands.block import Block
from .commands.nightmode import Nightmode
from .commands.imagine import AiStuffCog
from .commands.owner import Badges
from .commands.map import Map
from .commands.autoresponder import AutoResponder
from .commands.customrole import Customrole
from .commands.autorole import AutoRole
from .commands.antinuke import Antinuke
from .commands.extraown import Extraowner
from .commands.anti_wl import Whitelist
from .commands.anti_unwl import Unwhitelist
from .commands.slots import Slots
from .commands.blackjack import Blackjack
from .commands.autoreact import AutoReaction
from .commands.stats import Stats
from .commands.emergency import Emergency
from .commands.notify import NotifCommands
from .commands.status import Status
from .commands.np import NoPrefix
from .commands.filters import FilterCog
from .commands.owner2 import Global

# Events
from .events.autoblacklist import AutoBlacklist
from .events.Errors import Errors
from .events.on_guild import Guild
from .events.autorole import Autorole2
from .events.auto import Autorole
from .events.greet2 import greet
from .events.mention import Mention
from .events.react import React
from .events.autoreact import AutoReactListener

# Help Categories
from .olympus.antinuke import _antinuke
from .olympus.extra import _extra
from .olympus.general import _general
from .olympus.automod import _automod 
from .olympus.moderation import _moderation
from .olympus.fun import _fun
from .olympus.games import _games
from .olympus.ignore import _ignore
from .olympus.server import _server
from .olympus.voice import _voice 
from .olympus.welcome import _welcome 
from .olympus.giveaway import _giveaway

# Antinuke
from .antinuke.anti_member_update import AntiMemberUpdate
from .antinuke.antiban import AntiBan
from .antinuke.antibotadd import AntiBotAdd
from .antinuke.antichcr import AntiChannelCreate
from .antinuke.antichdl import AntiChannelDelete
from .antinuke.antichup import AntiChannelUpdate
from .antinuke.antieveryone import AntiEveryone
from .antinuke.antiguild import AntiGuildUpdate
from .antinuke.antiIntegration import AntiIntegration
from .antinuke.antikick import AntiKick
from .antinuke.antiprune import AntiPrune
from .antinuke.antirlcr import AntiRoleCreate
from .antinuke.antirldl import AntiRoleDelete
from .antinuke.antirlup import AntiRoleUpdate
from .antinuke.antiwebhook import AntiWebhookUpdate
from .antinuke.antiwebhookcr import AntiWebhookCreate
from .antinuke.antiwebhookdl import AntiWebhookDelete

# Automod
from .automod.antispam import AntiSpam
from .automod.anticaps import AntiCaps
from .automod.antilink import AntiLink
from .automod.anti_invites import AntiInvite
from .automod.anti_mass_mention import AntiMassMention
from .automod.anti_emoji_spam import AntiEmojiSpam

# Moderation
from .moderation.ban import Ban
from .moderation.unban import Unban
from .moderation.timeout import Mute
from .moderation.unmute import Unmute
from .moderation.lock import Lock
from .moderation.unlock import Unlock
from .moderation.hide import Hide
from .moderation.unhide import Unhide
from .moderation.kick import Kick
from .moderation.warn import Warn
from .moderation.role import Role
from .moderation.message import Message
from .moderation.moderation import Moderation
from .moderation.topcheck import TopCheck
from .moderation.snipe import Snipe


# ============================================
# AUTOMATIC COG LOADING SYSTEM
# ============================================

# Define cog groups for organized loading
COG_GROUPS = {
    "commands": [
        Help, General, Automod, Welcomer, Fun, Games, Extra, Voice, Owner,
        Customrole, afk, Embed, Media, Ignore, Invcrole, Giveaway, Steal,
        Ship, Timer, Blacklist, Block, Nightmode, AiStuffCog, Badges,
        Antinuke, Whitelist, Unwhitelist, Extraowner, Slots, Blackjack,
        Stats, Emergency, Status, NoPrefix, FilterCog, Global, Map
    ],
    "help_categories": [
        _antinuke, _extra, _general, _automod, _moderation, _fun, _games,
        _ignore, _server, _voice, _welcome, _giveaway
    ],
    "events": [
        AutoBlacklist, Guild, Errors, Autorole2, Autorole, greet,
        AutoResponder, Mention, AutoRole, React, AutoReaction, AutoReactListener,
        NotifCommands
    ],
    "antinuke": [
        AntiMemberUpdate, AntiBan, AntiBotAdd, AntiChannelCreate,
        AntiChannelDelete, AntiChannelUpdate, AntiEveryone, AntiGuildUpdate,
        AntiIntegration, AntiKick, AntiPrune, AntiRoleCreate, AntiRoleDelete,
        AntiRoleUpdate, AntiWebhookUpdate, AntiWebhookCreate, AntiWebhookDelete
    ],
    "automod": [
        AntiSpam, AntiCaps, AntiInvite, AntiLink, AntiMassMention, AntiEmojiSpam
    ],
    "moderation": [
        Ban, Unban, Mute, Unmute, Lock, Unlock, Hide, Unhide, Kick, Warn,
        Role, Message, Moderation, TopCheck, Snipe
    ]
}


async def setup(bot: Olympus):
    """
    Modern cog loader - automatically loads all cogs in organized groups.
    No need to manually add each cog to the list!
    """
    print(Fore.CYAN + Style.BRIGHT + "\n" + "="*50)
    print(Fore.CYAN + Style.BRIGHT + "🚀 Loading Cogs...")
    print(Fore.CYAN + Style.BRIGHT + "="*50 + "\n")
    
    total_loaded = 0
    total_failed = 0
    
    # Load cogs by group
    for group_name, cogs in COG_GROUPS.items():
        print(Fore.YELLOW + Style.BRIGHT + f"📦 Loading {group_name.upper()} cogs...")
        group_loaded = 0
        
        for cog in cogs:
            try:
                await bot.add_cog(cog(bot))
                print(Fore.GREEN + f"  ✅ {cog.__name__}")
                group_loaded += 1
                total_loaded += 1
            except Exception as e:
                print(Fore.RED + f"  ❌ Failed to load {cog.__name__}: {e}")
                total_failed += 1
        
        print(Fore.YELLOW + f"  └─ Loaded {group_loaded}/{len(cogs)} {group_name} cogs\n")
    
    # Summary
    print(Fore.CYAN + Style.BRIGHT + "="*50)
    print(Fore.GREEN + Style.BRIGHT + f"✨ Successfully loaded {total_loaded} cogs!")
    if total_failed > 0:
        print(Fore.RED + Style.BRIGHT + f"⚠️  Failed to load {total_failed} cogs")
    print(Fore.CYAN + Style.BRIGHT + "="*50 + "\n")
