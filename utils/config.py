"""
Centralized configuration for the Kyra Discord Bot.
All bot settings, tokens, colors, and emojis should be configured here.
"""
import os
from typing import List

# ============================================
# BOT CREDENTIALS & IDENTIFICATION
# ============================================
TOKEN = os.environ.get("TOKEN")
BOT_NAME = "Kyra✨"
BOT_ID = 1144179659735572640

# ============================================
# OWNER & ADMIN SETTINGS
# ============================================
OWNER_IDS: List[int] = [
    1341478551764860958,
    1179587826669592587,
    1204961543528382467
]

# ============================================
# SERVER LINKS
# ============================================
SUPPORT_SERVER = "https://discord.gg/X9NDdMf3xf"
SUPPORT_CHANNEL = "https://discord.com/channels/699587669059174461/1271825678710476911"

# ============================================
# BOT PREFIX
# ============================================
DEFAULT_PREFIX = "+"

# ============================================
# EMBED COLORS (Hex values)
# ============================================
class Colors:
    """Centralized color scheme for embeds"""
    DEFAULT = 0x000000      # Black
    SUCCESS = 0x00ff00      # Green
    ERROR = 0xff0000        # Red
    WARNING = 0xffa500      # Orange
    INFO = 0x00bfff         # Blue
    PREMIUM = 0xffd700      # Gold

# ============================================
# EMOJIS (Customize your emojis here)
# ============================================
class Emojis:
    """Centralized emoji configuration"""
    # Status emojis
    SUCCESS = "✅"
    ERROR = "❌"
    WARNING = "⚠️"
    INFO = "ℹ️"
    LOADING = "⏳"
    
    # Action emojis
    BAN = "🔨"
    KICK = "👢"
    MUTE = "🔇"
    UNMUTE = "🔊"
    LOCK = "🔒"
    UNLOCK = "🔓"
    
    # Feature emojis
    MUSIC = "🎵"
    GAMES = "🎮"
    MODERATION = "🛡️"
    ANTINUKE = "💣"
    AUTOMOD = "🤖"
    WELCOME = "👋"
    GIVEAWAY = "🎉"
    
    # Utility emojis
    SETTINGS = "⚙️"
    STATS = "📊"
    TIME = "⏰"
    STAR = "⭐"
    HEART = "❤️"

# ============================================
# LOGGING & WEBHOOKS
# ============================================
COMMAND_LOG_WEBHOOK = "https://discord.com/api/webhooks/1414341065217015808/CEsFE6FnH1HflbGlQR7KZszkht_r_-BKT03KJaRKg1lzUynaLcm_P6yZ5YN9Hr1tW9AC"

# ============================================
# GUILD NOTIFICATION CHANNELS
# ============================================
# Set these to None if you don't want notifications
GUILD_JOIN_CHANNEL_ID = None  # Channel ID for guild join notifications
GUILD_LEAVE_CHANNEL_ID = None  # Channel ID for guild leave notifications

# ============================================
# DEPRECATED/LEGACY NAMES (For backward compatibility)
# ============================================
NAME = BOT_NAME  # Deprecated - use BOT_NAME
BotName = BOT_NAME  # Deprecated - use BOT_NAME
server = SUPPORT_SERVER  # Deprecated - use SUPPORT_SERVER
serverLink = SUPPORT_SERVER  # Deprecated - use SUPPORT_SERVER
ch = SUPPORT_CHANNEL  # Deprecated - use SUPPORT_CHANNEL
