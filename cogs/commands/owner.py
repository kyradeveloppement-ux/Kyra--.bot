# owner_and_badges.py
from __future__ import annotations
import os
import json
import datetime
import asyncio
from io import BytesIO
from collections import Counter
from typing import Optional

import discord
from discord import Embed
from discord.ext import commands
from discord.ui import View, Button
from discord.errors import Forbidden

from PIL import Image, ImageDraw, ImageFont

import aiosqlite
import aiohttp

# utils (assumed existing)
from utils import Paginator, DescriptionEmbedPaginator, FieldPagePaginator, TextPaginator
from utils.Tools import *  # restart_program, blacklist_check, ignore_check, ... (assumed)
from utils.config import OWNER_IDS
from core import Cog, Olympus, Context  # depending on your project structure

# ---------------------------
# Config & constants
# ---------------------------
BADGE_URLS = {
    "owner": "https://cdn.discordapp.com/emojis/1228227536207740989.png",
    "staff": "https://cdn.discordapp.com/emojis/1228227884481515613.png",
    "partner": "https://cdn.discordapp.com/emojis/1228228301089144976.png",
    "sponsor": "https://cdn.discordapp.com/emojis/1228246375180013678.png",
    "friend": "https://cdn.discordapp.com/emojis/1228229690376982549.png",
    "early": "https://cdn.discordapp.com/emojis/1228241490246111302.png",
    "vip": "https://cdn.discordapp.com/emojis/1228230884583276584.png",
    "bug": "https://cdn.discordapp.com/emojis/1228231513456382015.png"
}

BADGE_NAMES = {
    "owner": "Owner",
    "staff": "Staff",
    "partner": "Partner",
    "sponsor": "Sponsor",
    "friend": "Owner's Friend",
    "early": "Early Supporter",
    "vip": "VIP",
    "bug": "Bug Hunter"
}

# File/database paths
DB_FOLDER = "db"
os.makedirs(DB_FOLDER, exist_ok=True)
BADGES_DB_FILE = os.path.join(DB_FOLDER, "badges.db")  # primary badges DB (async)
NP_DB_FILE = os.path.join(DB_FOLDER, "np.db")         # used for staff table (async)

FONT_PATH = os.path.join("utils", "arial.ttf")
if not os.path.isfile(FONT_PATH):
    # fallback to a PIL default font if arial not available
    from PIL import ImageFont as _IF
    try:
        _IF.truetype("arial.ttf", 14)
    except Exception:
        FONT_PATH = None  # will use default font from PIL when needed

# ---------------------------
# Utility helpers
# ---------------------------

def owner_or_staff():
    """decorator check: owner or staff from our staff table in cog"""
    async def predicate(ctx):
        cog = ctx.cog
        if ctx.author.id in OWNER_IDS:
            return True
        if cog is None:
            return False
        return getattr(cog, "staff", set()) and ctx.author.id in getattr(cog, "staff", set())
    return commands.check(predicate)


def convert_time_to_timedelta(time_str: str) -> datetime.timedelta:
    """
    Converts a string like '1h', '2d', '30m' into timedelta.
    Note: here 'm' = minutes (not months), to avoid invalid timedelta keyword.
    """
    units = {"h": "hours", "d": "days", "m": "minutes"}
    if not time_str:
        raise ValueError("time_str is empty")
    try:
        num = int(time_str[:-1])
        unit_char = time_str[-1]
        unit_name = units.get(unit_char)
        if not unit_name:
            raise ValueError("Invalid time unit")
        return datetime.timedelta(**{unit_name: num})
    except Exception as e:
        raise ValueError(f"Invalid time format: {time_str}") from e


# ---------------------------
# Async DB badge functions (aiosqlite)
# ---------------------------

async def ensure_badges_table():
    """Ensure badges table exists (async)."""
    async with aiosqlite.connect(BADGES_DB_FILE) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS badges (
                user_id INTEGER PRIMARY KEY,
                owner INTEGER DEFAULT 0,
                staff INTEGER DEFAULT 0,
                partner INTEGER DEFAULT 0,
                sponsor INTEGER DEFAULT 0,
                friend INTEGER DEFAULT 0,
                early INTEGER DEFAULT 0,
                vip INTEGER DEFAULT 0,
                bug INTEGER DEFAULT 0
            )
        ''')
        await db.commit()

async def add_badge(user_id: int, badge: str) -> bool:
    badge = badge.lower()
    if badge not in list(BADGE_URLS.keys()) + ["bug"]:
        return False
    async with aiosqlite.connect(BADGES_DB_FILE) as db:
        async with db.execute(f"SELECT {badge} FROM badges WHERE user_id = ?", (user_id,)) as cur:
            row = await cur.fetchone()
        if row is None:
            # insert new row with that badge = 1
            # build columns/values dynamically
            await db.execute(f"INSERT INTO badges (user_id, {badge}) VALUES (?, 1)", (user_id,))
            await db.commit()
            return True
        elif row[0] == 0:
            await db.execute(f"UPDATE badges SET {badge} = 1 WHERE user_id = ?", (user_id,))
            await db.commit()
            return True
        else:
            return False

async def remove_badge(user_id: int, badge: str) -> bool:
    badge = badge.lower()
    if badge not in list(BADGE_URLS.keys()) + ["bug"]:
        return False
    async with aiosqlite.connect(BADGES_DB_FILE) as db:
        async with db.execute(f"SELECT {badge} FROM badges WHERE user_id = ?", (user_id,)) as cur:
            row = await cur.fetchone()
        if row and row[0] == 1:
            await db.execute(f"UPDATE badges SET {badge} = 0 WHERE user_id = ?", (user_id,))
            await db.commit()
            return True
        return False

async def fetch_user_badges(user_id: int) -> dict:
    """Return dict badge -> 0/1 for given user"""
    cols = ["user_id"] + list(BADGE_URLS.keys())
    async with aiosqlite.connect(BADGES_DB_FILE) as db:
        async with db.execute("SELECT user_id, owner, staff, partner, sponsor, friend, early, vip, bug FROM badges WHERE user_id = ?", (user_id,)) as cur:
            row = await cur.fetchone()
    if not row:
        return {k: 0 for k in BADGE_URLS.keys()}
    else:
        # zip only badge keys (skip user_id)
        return dict(zip(cols, row))  # includes user_id - caller can ignore


# ---------------------------
# Removal helper (purge)
# ---------------------------
async def do_removal(ctx, limit, predicate, *, before=None, after=None):
    """Purge messages with safe error messages (async)."""
    if limit > 2000:
        return await ctx.send(f"Too many messages to search given ({limit}/2000)")

    if before is None:
        before_obj = ctx.message
    else:
        before_obj = discord.Object(id=before)

    after_obj = None
    if after is not None:
        after_obj = discord.Object(id=after)

    try:
        deleted_messages = await ctx.channel.purge(limit=limit, before=before_obj, after=after_obj, check=predicate)
    except discord.Forbidden:
        return await ctx.send("I do not have permissions to delete messages.")
    except discord.HTTPException as e:
        return await ctx.send(f"Error while purging messages: {e} (try a smaller search?)")

    spammers = Counter(m.author.display_name for m in deleted_messages)
    deleted_count = len(deleted_messages)

    if deleted_count == 0:
        return await ctx.send("No messages were removed.", delete_after=5)

    lines = [f'🧑‍💻 | {deleted_count} message{" was" if deleted_count == 1 else "s were"} removed.']
    spammers_sorted = sorted(spammers.items(), key=lambda t: t[1], reverse=True)
    lines.append("")
    lines.extend(f"**{name}**: {count}" for name, count in spammers_sorted)

    resp = "\n".join(lines)
    if len(resp) > 2000:
        await ctx.send(f"🧑‍💻 | Successfully removed {deleted_count} messages.", delete_after=5)
    else:
        await ctx.send(resp, delete_after=5)


# ---------------------------
# Cogs
# ---------------------------

class Owner(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.db_path = NP_DB_FILE
        self.staff = set()
        self.np_cache = []
        self.stop_tour = False
        self.bot_owner_ids = OWNER_IDS
        # schedule DB setup and staff load
        self.client.loop.create_task(self._async_init())

    async def _async_init(self):
        # ensure DBs exist
        await ensure_badges_table()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('CREATE TABLE IF NOT EXISTS staff (id INTEGER PRIMARY KEY)')
            await db.commit()
        # load staff
        await self.load_staff()

    async def load_staff(self):
        await self.client.wait_until_ready()
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('SELECT id FROM staff') as cur:
                rows = await cur.fetchall()
        self.staff = {row[0] for row in rows}

    # --- staff management ---
    @commands.command(name="staff_add", aliases=["staffadd", "addstaff"], help="Adds a user to the staff list.")
    @commands.is_owner()
    async def staff_add(self, ctx, user: discord.User):
        if user.id in self.staff:
            embed = discord.Embed(title="Access Denied", description=f"{user} is already in the staff list.", color=0x000000)
            return await ctx.reply(embed=embed, mention_author=False)
        self.staff.add(user.id)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('INSERT OR IGNORE INTO staff (id) VALUES (?)', (user.id,))
            await db.commit()
        embed = discord.Embed(title="✅ Success", description=f"Added {user} to the staff list.", color=0x000000)
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="staff_remove", aliases=["staffremove", "removestaff"], help="Removes a user from the staff list.")
    @commands.is_owner()
    async def staff_remove(self, ctx, user: discord.User):
        if user.id not in self.staff:
            embed = discord.Embed(title="❌ Access Denied", description=f"{user} is not in the staff list.", color=0x000000)
            return await ctx.reply(embed=embed, mention_author=False)
        self.staff.remove(user.id)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('DELETE FROM staff WHERE id = ?', (user.id,))
            await db.commit()
        embed = discord.Embed(title="✅ Success", description=f"Removed {user} from the staff list.", color=0x000000)
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="staff_list", aliases=["stafflist", "liststaff", "staffs"], help="Lists all staff members.")
    @commands.is_owner()
    async def staff_list(self, ctx):
        if not self.staff:
            return await ctx.send("The staff list is currently empty.")
        member_list = []
        for staff_id in self.staff:
            try:
                member = await self.client.fetch_user(staff_id)
                member_list.append(f"{member.name}#{member.discriminator} (ID: {staff_id})")
            except Exception:
                member_list.append(f"<Unknown user> (ID: {staff_id})")
        staff_display = "\n".join(member_list)
        sonu = discord.Embed(title="m🐍 Kyra✨ Staffs", description=f"\n{staff_display}", color=0x000000)
        await ctx.send(embed=sonu)

    # --- server list ---
    @commands.command(name="servlist")
    @commands.check(owner_or_staff())
    async def _slist(self, ctx):
        sonuop = sorted(self.client.guilds, key=lambda g: g.member_count, reverse=True)
        entries = [
            f"`#{i}` | [{g.name}](https://discord.com/guilds/{g.id}) - {g.member_count}"
            for i, g in enumerate(sonuop, start=1)
        ]
        embeds = DescriptionEmbedPaginator(
            entries=entries,
            description="",
            title=f"Guild List of Kyra [{len(self.client.guilds)}]",
            color=0x000000,
            per_page=10
        ).get_pages()
        paginator = Paginator(ctx, embeds)
        await paginator.paginate()

    # --- mutual servers ---
    @commands.command(name="mutual", aliases=["mutuals"])
    @commands.is_owner()
    async def mutual_servers(self, ctx: Context, user: discord.User):
        if not user:
            return await ctx.send("User not found.")
        mutual_guilds = [guild for guild in self.client.guilds if guild.get_member(user.id) is not None]
        if mutual_guilds:
            entries = [
                f"`{no}` | [{guild.name}](https://discord.com/channels/{guild.id}) (ID: {guild.id})"
                for no, guild in enumerate(mutual_guilds, start=1)
            ]
            embeds = DescriptionEmbedPaginator(
                entries=entries,
                title=f"Mutual Guilds with {user.name} [{len(mutual_guilds)}]",
                description="",
                per_page=10,
                color=0x00ff00
            ).get_pages()
            paginator = Paginator(ctx, embeds)
            await paginator.paginate()
        else:
            await ctx.send("No mutual guilds found.")

    # --- getinvite ---
    @commands.command(name="getinvite", aliases=["gi", "getinvites"], help="Get invites for a guild or channel.")
    @commands.is_owner()
    async def getinvite(self, ctx, guild_id: int = None, channel_id: int = None):
        guild = None
        channel = None

        if guild_id:
            guild = self.client.get_guild(guild_id)
            if not guild:
                return await ctx.send("Invalid guild ID.")
        elif channel_id:
            channel = self.client.get_channel(channel_id)
            if not channel:
                return await ctx.send("Invalid channel ID.")
            guild = channel.guild
        else:
            return await ctx.send("Please provide a guild ID or channel ID.")

        can_create_invites = (guild.me.guild_permissions.create_instant_invite) if guild else False

        try:
            if guild_id:
                invites = await guild.invites()
                if invites:
                    invites_list = [f"{invite.url} - {invite.uses} uses" for invite in invites]
                    embeds = DescriptionEmbedPaginator(
                        entries=invites_list,
                        title=f"Active Invites for {guild.name}",
                        description="",
                        per_page=10,
                        color=0xff0000
                    ).get_pages()
                    paginator = Paginator(ctx, embeds)
                    await paginator.paginate()
                elif can_create_invites:
                    channel_to_use = guild.system_channel or next(
                        (ch for ch in guild.text_channels if ch.permissions_for(guild.me).create_instant_invite),
                        None
                    )
                    if channel_to_use:
                        invite = await channel_to_use.create_invite(max_age=604800, max_uses=None, reason="No active invites found, creating a new one.")
                        await ctx.send(f"Created new invite: {invite.url}")
                    else:
                        await ctx.send("No suitable channel found to create an invite.")
                else:
                    await ctx.send("Bot lacks permission to create invites for the guild.")

            elif channel_id:
                if channel.permissions_for(guild.me).create_instant_invite:
                    invite = await channel.create_invite(max_age=604800, max_uses=None, reason="Creating invite for the specified channel.")
                    await ctx.send(f"Created new invite for the channel: {invite.url}")
                else:
                    await ctx.send("Bot lacks permission to create invites for the specified channel.")
        except discord.Forbidden:
            await ctx.send("Bot lacks permission to access or create invites.")
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

    # --- getguild (from channel id) ---
    @commands.command(name="getguild")
    @commands.is_owner()
    async def get_guild(self, ctx, channel_id: int):
        channel = self.client.get_channel(channel_id)
        if channel:
            guild = channel.guild
            embed = discord.Embed(title=f"Guild Information for {guild.name}", color=0x000000)
            embed.add_field(name="Guild Name", value=guild.name, inline=True)
            embed.add_field(name="Guild ID", value=guild.id, inline=True)
            embed.add_field(name="Member Count", value=guild.member_count, inline=True)
            embed.add_field(name="Owner", value=str(guild.owner), inline=True)
            embed.add_field(name="Created At", value=guild.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=True)
            await ctx.send(embed=embed)
        else:
            await ctx.send("Invalid channel ID or bot has no access to the channel.")

    # --- restart ---
    @commands.command(name="kyra.restart", help="Restarts the client.")
    @commands.is_owner()
    async def _restart(self, ctx: Context):
        await ctx.reply("Restarting Kyra...")
        try:
            restart_program()  # from utils.Tools
        except Exception as e:
            await ctx.send(f"Failed to restart: {e}")

    # --- sync (fix JSON keys, safer) ---
    @commands.command(name="sync", help="Syncs all database.")
    @commands.is_owner()
    async def _sync(self, ctx):
        await ctx.reply("Syncing...", mention_author=False)
        try:
            with open('events.json', 'r') as f:
                data = json.load(f)
        except Exception:
            data = {}
        # guard keys
        if 'guilds' not in data:
            data['guilds'] = {}
        for guild in self.client.guilds:
            if str(guild.id) not in data['guilds']:
                data['guilds'][str(guild.id)] = 'on'
        with open('events.json', 'w') as f:
            json.dump(data, f, indent=4)

        # config cleanup
        try:
            with open('config.json', 'r') as f:
                cfg = json.load(f)
        except Exception:
            cfg = {"guilds": {}}
        # remove missing guilds
        for op in list(cfg.get("guilds", {}).keys()):
            g = self.client.get_guild(int(op))
            if not g:
                cfg["guilds"].pop(op, None)
        with open('config.json', 'w') as f:
            json.dump(cfg, f, indent=4)

    # --- owners (found) ---
    @commands.command(name="found")
    @commands.is_owner()
    async def own_list(self, ctx):
        nplist = OWNER_IDS
        npl = []
        for uid in nplist:
            try:
                npl.append(await self.client.fetch_user(uid))
            except Exception:
                # skip if fetch fails
                pass
        npl_sorted = sorted(npl, key=lambda u: u.created_at if getattr(u, "created_at", None) else datetime.datetime.utcnow())
        entries = [
            f"`#{no}` | [{mem}](https://discord.com/users/{mem.id}) (ID: {mem.id})"
            for no, mem in enumerate(npl_sorted, start=1)
        ]
        embeds = DescriptionEmbedPaginator(
            entries=entries,
            title=f"Kyra Owners [{len(npl)}]",
            description="",
            per_page=10,
            color=0x000000
        ).get_pages()
        paginator = Paginator(ctx, embeds)
        await paginator.paginate()

    # --- dm ---
    @commands.command()
    @commands.is_owner()
    async def dm(self, ctx, user: discord.User, *, message: str):
        """ DM the user of your choice """
        try:
            await user.send(message)
            await ctx.send(f"✅ | Successfully Sent a DM to **{user}**")
        except discord.Forbidden:
            await ctx.send("This user might be having DMs blocked or it's a bot account...")

    # --- change nickname ---
    @commands.group()
    @commands.is_owner()
    async def change(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(str(ctx.command))

    @change.command(name="nickname")
    @commands.is_owner()
    async def change_nickname(self, ctx, *, name: str = None):
        """ Change nickname. """
        try:
            await ctx.guild.me.edit(nick=name)
            if name:
                await ctx.send(f"✅ | Successfully changed nickname to **{name}**")
            else:
                await ctx.send("✅ | Successfully removed nickname")
        except Exception as err:
            await ctx.send(err)

    # --- owner ban/unban/globalunban/guildban/guildunban/leaveguild ---
    @commands.command(name="ownerban", aliases=["forceban", "dna"])
    @commands.is_owner()
    async def _ownerban(self, ctx: Context, user_id: int, *, reason: str = "No reason provided"):
        member = ctx.guild.get_member(user_id)
        try:
            if member:
                await member.ban(reason=reason)
                embed = discord.Embed(
                    title="Successfully Banned",
                    description=f"✅ | **{member.name}** has been successfully banned from {ctx.guild.name} by the Bot Owner.",
                    color=0x000000)
                await ctx.reply(embed=embed, mention_author=False, delete_after=3)
                try:
                    await ctx.message.delete()
                except Exception:
                    pass
            else:
                # ban by id
                obj = discord.Object(id=user_id)
                await ctx.guild.ban(obj, reason=reason)
                await ctx.reply(f"Successfully banned user ID {user_id}.", mention_author=False)
        except discord.Forbidden:
            embed = discord.Embed(
                title="Error!",
                description=f"😌 I do not have permission to ban that user in this guild.",
                color=0x000000)
            await ctx.reply(embed=embed, mention_author=False, delete_after=5)
        except discord.HTTPException:
            embed = discord.Embed(
                title="Error!",
                description=f"😤 An error occurred while banning the user.",
                color=0x000000)
            await ctx.reply(embed=embed, mention_author=False, delete_after=5)

    @commands.command(name="ownerunban", aliases=["forceunban"])
    @commands.is_owner()
    async def _ownerunban(self, ctx: Context, user_id: int, *, reason: str = "No reason provided"):
        try:
            user = await self.client.fetch_user(user_id)
            user_obj = discord.Object(id=user_id)
            await ctx.guild.unban(user_obj, reason=reason)
            embed = discord.Embed(
                title="Successfully Unbanned",
                description=f"🐍 | **{user.name}** has been successfully unbanned from {ctx.guild.name} by the Bot Owner.",
                color=0x000000
            )
            await ctx.reply(embed=embed, mention_author=False)
        except discord.Forbidden:
            embed = discord.Embed(
                title="Error!",
                description=f"😄 I do not have permission to unban that user in this guild.",
                color=0x000000
            )
            await ctx.reply(embed=embed, mention_author=False)
        except discord.NotFound:
            await ctx.reply("User not found.", mention_author=False)
        except discord.HTTPException:
            await ctx.reply("An error occurred while trying to unban the user.", mention_author=False)

    @commands.command(name="globalunban")
    @commands.is_owner()
    async def globalunban(self, ctx: Context, user: discord.User):
        success_guilds = []
        error_guilds = []

        for guild in self.client.guilds:
            try:
                bans = await guild.bans()
            except Exception:
                continue
            if any(ban_entry.user.id == user.id for ban_entry in bans):
                try:
                    await guild.unban(user, reason="Global Unban")
                    success_guilds.append(guild.name)
                except (discord.HTTPException, discord.Forbidden):
                    error_guilds.append(guild.name)

        user_mention = f"{user.mention} (**{user.name}**)"
        success_message = f"Successfully unbanned {user_mention} from: {', '.join(success_guilds)}" if success_guilds else "No guilds where the user was successfully unbanned."
        error_message = f"Failed to unban {user_mention} from: {', '.join(error_guilds)}" if error_guilds else "No errors during unbanning."
        await ctx.reply(f"{success_message}\n{error_message}", mention_author=False)

    @commands.command(name="guildban")
    @commands.is_owner()
    async def guildban(self, ctx: Context, guild_id: int, user_id: int, *, reason: str = "No reason provided"):
        guild = self.client.get_guild(guild_id)
        if not guild:
            return await ctx.reply("Bot is not present in the specified guild.", mention_author=False)
        member = guild.get_member(user_id)
        try:
            if member:
                await guild.ban(member, reason=reason)
                await ctx.reply(f"Successfully banned **{member.name}** from {guild.name}.", mention_author=False)
            else:
                obj = discord.Object(id=user_id)
                await guild.ban(obj, reason=reason)
                await ctx.reply(f"Successfully banned user ID {user_id} from {guild.name}.", mention_author=False)
        except discord.Forbidden:
            await ctx.reply(f"Missing permissions to ban in {guild.name}.", mention_author=False)
        except discord.HTTPException as e:
            await ctx.reply(f"An error occurred while banning in {guild.name}: {e}", mention_author=False)

    @commands.command(name="guildunban")
    @commands.is_owner()
    async def guildunban(self, ctx: Context, guild_id: int, user_id: int, *, reason: str = "No reason provided"):
        guild = self.client.get_guild(guild_id)
        if not guild:
            return await ctx.reply("Bot is not present in the specified guild.", mention_author=False)
        try:
            user_obj = discord.Object(id=user_id)
            await guild.unban(user_obj, reason=reason)
            await ctx.reply(f"Successfully unbanned user ID {user_id} from {guild.name}.", mention_author=False)
        except discord.Forbidden:
            await ctx.reply(f"Missing permissions to unban in {guild.name}.", mention_author=False)
        except discord.HTTPException as e:
            await ctx.reply(f"An error occurred while unbanning in {guild.name}: {e}", mention_author=False)

    @commands.command(name="leaveguild")
    @commands.is_owner()
    async def leave_guild(self, ctx, guild_id: int):
        guild = self.client.get_guild(guild_id)
        if guild is None:
            return await ctx.send(f"Guild with ID {guild_id} not found.")
        await guild.leave()
        await ctx.send(f"Left the guild: {guild.name} ({guild.id})")

    # --- guildinfo (owner or staff) ---
    @commands.command(name="guildinfo")
    @commands.check(owner_or_staff())
    async def guild_info(self, ctx, guild_id: int):
        guild = self.client.get_guild(guild_id)
        if guild is None:
            return await ctx.send(f"Guild with ID {guild_id} not found.")
        embed = discord.Embed(title=guild.name, description=f"Information for guild ID {guild.id}", color=discord.Color.blue())
        embed.add_field(name="Owner", value=str(guild.owner), inline=True)
        embed.add_field(name="Member Count", value=str(guild.member_count), inline=True)
        embed.add_field(name="Text Channels", value=str(len(guild.text_channels)), inline=True)
        embed.add_field(name="Voice Channels", value=str(len(guild.voice_channels)), inline=True)
        embed.add_field(name="Roles", value=str(len(guild.roles)), inline=True)
        if guild.icon is not None and guild.icon.url:
            embed.set_thumbnail(url=guild.icon.url)
        embed.set_footer(text=f"Created at: {guild.created_at}")
        await ctx.send(embed=embed)

    # --- servertour ---
    @commands.command()
    @commands.is_owner()
    async def servertour(self, ctx, time_in_seconds: int, member: discord.Member):
        guild = ctx.guild
        if time_in_seconds > 3600:
            return await ctx.send("Time cannot be greater than 3600 seconds (1 hour).")
        if not member.voice:
            return await ctx.send(f"{member.display_name} is not in a voice channel.")
        voice_channels = [ch for ch in guild.voice_channels if ch.permissions_for(guild.me).move_members]
        if len(voice_channels) < 2:
            return await ctx.send("Not enough voice channels to move the user.")
        self.stop_tour = False

        class StopButton(View):
            def __init__(self, outer_self):
                super().__init__(timeout=time_in_seconds)
                self.outer_self = outer_self

            @discord.ui.button(label="Stop", style=discord.ButtonStyle.danger)
            async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user.id not in self.outer_self.bot_owner_ids:
                    await interaction.response.send_message("Only the bot owner can stop this process.", ephemeral=True)
                    return
                self.outer_self.stop_tour = True
                await interaction.response.send_message("Server tour has been stopped.", ephemeral=True)
                self.stop()

        view = StopButton(self)
        message = await ctx.send(f"Started moving {member.display_name} for {time_in_seconds} seconds. Click the button to stop.", view=view)
        end_time = asyncio.get_event_loop().time() + time_in_seconds

        try:
            while asyncio.get_event_loop().time() < end_time and not self.stop_tour:
                for ch in voice_channels:
                    if self.stop_tour:
                        await ctx.send("Tour stopped.")
                        return
                    if not member.voice:
                        await ctx.send(f"{member.display_name} left the voice channel.")
                        return
                    try:
                        await member.move_to(ch)
                        await asyncio.sleep(1)
                    except Forbidden:
                        await ctx.send(f"Missing permissions to move {member.display_name}.")
                        return
                    except Exception as e:
                        await ctx.send(f"Error: {str(e)}")
                        return
        finally:
            if not self.stop_tour:
                try:
                    await message.edit(content=f"Finished moving {member.display_name} after {time_in_seconds} seconds.", view=None)
                except Exception:
                    pass

    # --- badges group (add/remove) ---
    @commands.group()
    @commands.check(owner_or_staff())
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def bdg(self, ctx):
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(description='Invalid `bdg` command passed. Use `add` or `remove`.', color=0x000000)
            await ctx.send(embed=embed)

    @bdg.command()
    @commands.check(owner_or_staff())
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def add(self, ctx, member: discord.Member, badge: str):
        badge = badge.lower()
        user_id = member.id
        if badge in BADGE_URLS.keys() or badge == 'bug' or badge == 'all':
            if badge == 'all':
                for b in BADGE_URLS.keys():
                    await add_badge(user_id, b)
                await add_badge(user_id, 'bug')
                embed = discord.Embed(description=f"All badges added to {member.mention}.", color=0x000000)
                await ctx.send(embed=embed)
            else:
                success = await add_badge(user_id, badge)
                if success:
                    embed = discord.Embed(description=f"Badge `{badge}` added to {member.mention}.", color=0x000000)
                else:
                    embed = discord.Embed(description=f"{member.mention} already has the badge `{badge}` or badge invalid.", color=0x000000)
                await ctx.send(embed=embed)
        else:
            embed = discord.Embed(description=f"Invalid badge: `{badge}`", color=0x000000)
            await ctx.send(embed=embed)

    @bdg.command()
    @commands.check(owner_or_staff())
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def remove(self, ctx, member: discord.Member, badge: str):
        badge = badge.lower()
        user_id = member.id
        if badge in BADGE_URLS.keys() or badge == 'bug' or badge == 'all':
            if badge == 'all':
                for b in BADGE_URLS.keys():
                    await remove_badge(user_id, b)
                await remove_badge(user_id, 'bug')
                embed = discord.Embed(description=f"All badges removed from {member.mention}.", color=0x000000)
                await ctx.send(embed=embed)
            else:
                success = await remove_badge(user_id, badge)
                if success:
                    embed = discord.Embed(description=f"Badge `{badge}` removed from {member.mention}.", color=0x000000)
                else:
                    embed = discord.Embed(description=f"{member.mention} does not have the badge `{badge}`.", color=0x000000)
                await ctx.send(embed=embed)
        else:
            embed = discord.Embed(description=f"Invalid badge: `{badge}`", color=0x000000)
            await ctx.send(embed=embed)

    # --- forcepurgebots / forcepurgeuser ---
    @commands.command(name="forcepurgebots", aliases=["fpb"], help="Clear recently bot messages in channel (Bot owner only)")
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.is_owner()
    @commands.bot_has_permissions(manage_messages=True)
    async def _purgebot(self, ctx, prefix: Optional[str] = None, search: int = 100):
        try:
            await ctx.message.delete()
        except Exception:
            pass

        def predicate(m):
            return (m.webhook_id is None and m.author.bot) or (prefix and m.content.startswith(prefix))

        await do_removal(ctx, search, predicate)

    @commands.command(name="forcepurgeuser", aliases=["fpu"], help="Clear recent messages of a user in channel (Bot owner only)")
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.is_owner()
    @commands.bot_has_permissions(manage_messages=True)
    async def purguser(self, ctx, member: discord.Member, search: int = 100):
        try:
            await ctx.message.delete()
        except Exception:
            pass
        await do_removal(ctx, search, lambda e: e.author == member)

    # --- owner.help ---
    @commands.command(name="owner.help", aliases=['ownerhelp', 'owner-help'], hidden=True)
    @commands.is_owner()
    async def _owner_help(self, ctx):
        embed = Embed(title="Owner Commands",
                      description="`staffadd` ,   `staffremove` ,   `stafflist` , `slist` ,   `getinvite <guild-id>` ,   `getguild <channel-id>` ,   `mutual <user>` ,   `guildban <guild_id> <user_id>` ,   `guildunban <guild_id> <user_id>` ,   `kyra.restart` ,   `servertour` ,   `forcepurgebots` , `forcepurgeuser` ,   `ownerban` , `bdg add <user> <badge>` ,   `bdg remove <user> <badge>` ,   `global <subcommand>` ,   `np <subcommand>` ,   `autonp <subcommand>`",
                      color=0x000000)
        await ctx.send(embed=embed)


class Badges(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # ensure badge table will exist (fire-and-forget)
        bot.loop.create_task(ensure_badges_table())

    @commands.hybrid_command(aliases=['profile', 'pr'])
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def badges(self, ctx, member: discord.Member = None):
        processing_message = await ctx.send("⌛ Loading your profile...")
        member = member or ctx.author
        user_id = member.id

        # fetch badges (async)
        badges_row = await fetch_user_badges(user_id)  # returns dict including user_id

        # normalize dict: keys may include user_id
        if "user_id" in badges_row:
            # strip user_id
            badge_values = {k: badges_row[k] for k in badges_row.keys() if k != "user_id"}
        else:
            badge_values = badges_row

        has_badges = any(v == 1 for v in badge_values.values())

        # prepare embed common fields
        embed = discord.Embed(title=f"{member.display_name}'s Profile", color=0x000000)
        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url)
        else:
            embed.set_thumbnail(url=member.default_avatar.url)

        # created/joined timestamps (safe checks)
        try:
            embed.add_field(name="__**Account Created At**__", value=f"<t:{int(member.created_at.timestamp())}:F>", inline=True)
        except Exception:
            embed.add_field(name="__**Account Created At**__", value="Unknown", inline=True)
        try:
            embed.add_field(name="__**Joined This Guild At**__", value=f"<t:{int(member.joined_at.timestamp())}:F>", inline=True)
        except Exception:
            embed.add_field(name="__**Joined This Guild At**__", value="Unknown", inline=True)

        # user public flags -> friendly badges
        user_flags = member.public_flags
        user_badges = []

        badge_mapping = {
            "staff": "🧑‍💻 Discord Employee",
            "partner": "⛓️ Partnered Server Owner",
            "discord_certified_moderator": "🧑‍🍳 Moderator Programs Alumni",
            "hypesquad_balance": "House Balance Member",
            "hypesquad_bravery": "House Bravery Member",
            "hypesquad_brilliance": "House Brilliance Member",
            "hypesquad": "HypeSquad Events Member",
            "early_supporter": "🤩 Early Supporter",
            "bug_hunter": "👹 Bug Hunter Level 1",
            "bug_hunter_level_2": "👹 Bug Hunter Level 2",
            "verified_bot": "✅ Verified Bot",
            "verified_bot_developer": "🧑‍💻 Verified Bot Developer",
            "active_developer": "🧑‍💻 Active Developer",
            "early_verified_bot_developer": "✅ Early Verified Bot Developer",
            "system": "📣 System User",
            "team_user": "👷 User is a Team",
            "spammer": "😤 Marked as Spammer",
            "bot_http_interactions": "<:HTTP_INTERACTION_BOT:1274719023401013279> Bot uses only HTTP interactions"
        }

        for flag, label in badge_mapping.items():
            if getattr(user_flags, flag, False):
                user_badges.append(label)

        # Nitro/Booster heuristics
        try:
            user = await self.bot.fetch_user(member.id)
            has_animated_avatar = bool(user.avatar and user.avatar.is_animated())
            has_banner = bool(getattr(user, "banner", None))
            if not member.bot:
                if has_banner or has_animated_avatar:
                    user_badges.append("🔮 Nitro Subscriber")
                # fast check for boosting: member.premium_since or member in premium_subscribers
                if getattr(member, "premium_since", None):
                    user_badges.append("m🔮 Server Booster Badge")
        except Exception:
            pass

        if user_badges:
            embed.add_field(name="__**User Badges**__", value="\n".join(user_badges), inline=False)
        else:
            embed.add_field(name="__**User Badges**__", value="None", inline=False)

        # Bot badges: from our badge table
        if has_badges:
            # Build image of badges async (fetch with aiohttp)
            badge_size = 120
            padding = 80
            num_columns = 4
            image_width = 960
            image_height = 540

            # prepare image
            img = Image.new('RGBA', (image_width, image_height), (255, 255, 255, 0))
            draw = ImageDraw.Draw(img)
            font = ImageFont.truetype(FONT_PATH, 25) if FONT_PATH else ImageFont.load_default()

            async def fetch_badge_bytes(url: str) -> BytesIO:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as resp:
                        data = await resp.read()
                return BytesIO(data)

            # layout
            upper_y = (image_height // 4) - (badge_size // 2)
            lower_y = (3 * image_height // 4) - (badge_size // 2)
            x_positions = [padding + i * ((image_width - 2 * padding) // (num_columns - 1)) for i in range(num_columns)]

            badge_positions = [b for b, v in badge_values.items() if v == 1]
            for i, badge in enumerate(badge_positions):
                y = upper_y if i < num_columns else lower_y
                x = x_positions[i % num_columns]
                try:
                    badge_bytes = await fetch_badge_bytes(BADGE_URLS[badge])
                    badge_img = Image.open(badge_bytes).convert("RGBA").resize((badge_size, badge_size))
                    img.paste(badge_img, (x - badge_size // 2, y), badge_img)
                    # draw label
                    text = BADGE_NAMES.get(badge, badge)
                    text_bbox = draw.textbbox((0, 0), text, font=font)
                    text_width = text_bbox[2] - text_bbox[0]
                    draw.text((x - text_width // 2, y + badge_size + 5), text, fill=(255, 0, 0), font=font)
                except Exception:
                    # if fetch fails, skip and continue
                    continue

            # save to bytes and attach
            with BytesIO() as image_binary:
                img.save(image_binary, 'PNG')
                image_binary.seek(0)
                file = discord.File(fp=image_binary, filename='badge.png')
                embed.add_field(name="__**Bot Badges**__", value="Below", inline=False)
                embed.set_image(url="attachment://badge.png")
                embed.set_footer(text=f"Requested by {ctx.author} | Nitro badge if banner/animated avatar; Booster badge if boosting a mutual guild with bot.", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
                await ctx.send(embed=embed, file=file)
                try:
                    await processing_message.delete()
                except Exception:
                    pass
                return

        # no badges
        embed.add_field(name="__**Bot Badges**__", value="No bot badges", inline=False)
        embed.set_footer(text=f"Requested by {ctx.author} | Nitro badge if banner/animated avatar; Booster badge if boosting a mutual guild with bot.", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        await ctx.send(embed=embed)
        try:
            await processing_message.delete()
        except Exception:
            pass


# ---------------------------
# Cog setup function (for extension)
# ---------------------------
async def setup(bot):
    await ensure_badges_table()
    await bot.add_cog(Owner(bot))
    await bot.add_cog(Badges(bot))
