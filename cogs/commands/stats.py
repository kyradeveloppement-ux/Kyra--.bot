import discord
import psutil
import os
import time
import aiosqlite
import platform
import importlib.metadata
import datetime
from discord import Embed, ButtonStyle
from discord.ui import Button, View
from discord.ext import commands
from utils.Tools import *
import wavelink


class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = time.time()
        self.total_songs_played = 0

        os.makedirs("db", exist_ok=True)
        self.bot.loop.create_task(self.setup_database())

    async def setup_database(self):
        async with aiosqlite.connect("db/stats.db") as db:
            await db.execute("CREATE TABLE IF NOT EXISTS stats (key TEXT PRIMARY KEY, value INTEGER)")
            await db.commit()
            async with db.execute("SELECT value FROM stats WHERE key = 'total_songs_played'") as cursor:
                row = await cursor.fetchone()
                self.total_songs_played = row[0] if row else 0

    async def update_total_songs_played(self):
        async with aiosqlite.connect("db/stats.db") as db:
            await db.execute(
                "INSERT OR REPLACE INTO stats (key, value) VALUES ('total_songs_played', ?)",
                (self.total_songs_played,),
            )
            await db.commit()

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload):
        self.total_songs_played += 1
        await self.update_total_songs_played()

    @commands.hybrid_command(
        name="stats",
        aliases=["botinfo", "botstats", "bi", "statistics"],
        help="Shows the bot's information.",
    )
    # ⚠️ laisse blacklist_check et ignore_check de côté pour tester
    # @blacklist_check()
    # @ignore_check()
    @commands.cooldown(1, 7, commands.BucketType.user)
    async def stats(self, ctx):
        print(f"➡️ /stats exécuté par {ctx.author} dans {ctx.guild}")

        processing_message = await ctx.send("⚙️ Loading Kyra✨ information...")

        try:
            # --- Guilds et Users
            guild_count = len(self.bot.guilds)
            user_count = sum(g.member_count for g in self.bot.guilds if g.member_count is not None)
            bot_count = sum(sum(1 for m in g.members if m.bot) for g in self.bot.guilds)
            human_count = user_count - bot_count
            print(f"📊 guilds={guild_count}, users={user_count}, humans={human_count}, bots={bot_count}")

            # --- Uptime
            uptime_seconds = int(round(time.time() - self.start_time))
            uptime_timedelta = datetime.timedelta(seconds=uptime_seconds)
            uptime = (
                f"{uptime_timedelta.days} days, "
                f"{uptime_timedelta.seconds // 3600} hours, "
                f"{(uptime_timedelta.seconds // 60) % 60} minutes, "
                f"{uptime_timedelta.seconds % 60} seconds"
            )
            print("🟢 uptime =", uptime)

            # --- Stats système
            cpu_info = psutil.cpu_freq() or psutil._common.scpufreq(0, 0, 0)
            memory_info = psutil.virtual_memory()
            total_libraries = len(importlib.metadata.distributions())

            # --- Musique
            channels_connected = sum(1 for vc in self.bot.voice_clients if vc)
            playing_tracks = sum(1 for vc in self.bot.voice_clients if getattr(vc, "playing", False))

            # --- Embed principal
            embed = Embed(title="Kyra Statistics: General", color=0x000000)
            embed.add_field(
                name="💃 Users",
                value=f"Humans: **{human_count}** | Bots: **{bot_count}**",
                inline=False,
            )
            embed.add_field(name="🟢 Uptime", value=f"{uptime}", inline=False)
            embed.add_field(name="📊 Guilds", value=f"{guild_count}", inline=False)
            embed.add_field(
                name="🎧 Music Stats",
                value=f"Connected: {channels_connected} | Playing: {playing_tracks} | Total Played: {self.total_songs_played}",
                inline=False,
            )
            embed.add_field(
                name="🐍 Libraries Used",
                value=f"Discord.py: **{discord.__version__}**\nTotal Libraries: **{total_libraries}**",
                inline=False,
            )

            # Footer
            embed.set_footer(text="Powered by Kyra✨ Development™", icon_url=self.bot.user.display_avatar.url)

            # --- Boutons
            view = View()

            # Bouton General
            general_button = Button(label="General", style=ButtonStyle.gray)
            async def general_button_callback(interaction):
                if interaction.user == ctx.author:
                    await interaction.response.edit_message(embed=embed, view=view)
            general_button.callback = general_button_callback
            view.add_item(general_button)

            # Bouton System
            system_button = Button(label="System", style=ButtonStyle.gray)
            async def system_button_callback(interaction):
                if interaction.user == ctx.author:
                    system_embed = Embed(title="Kyra Statistics: System", color=0x000000)
                    system_embed.add_field(
                        name="🧶 System Info",
                        value=f"Python: {platform.python_version()} | OS: {platform.system()} {platform.release()}",
                        inline=False,
                    )
                    system_embed.add_field(
                        name="🎴 Memory Info",
                        value=f"Total: {memory_info.total / (1024 ** 2):,.2f} MB | Used: {memory_info.used / (1024 ** 2):,.2f} MB",
                        inline=False,
                    )
                    system_embed.add_field(
                        name="🖥️ CPU Info",
                        value=f"Cores: {psutil.cpu_count(logical=False)} | Usage: {psutil.cpu_percent()}%",
                        inline=False,
                    )
                    await interaction.response.edit_message(embed=system_embed, view=view)
            system_button.callback = system_button_callback
            view.add_item(system_button)

            # Bouton Team
            team_button = Button(label="Team", style=ButtonStyle.primary)
            async def team_button_callback(interaction):
                if interaction.user == ctx.author:
                    team_embed = Embed(title="Kyra Team", color=0x000000)
                    team_embed.add_field(
                        name="👑 Bot Owners",
                        value=">>> [Natrix](https://discord.com/users/1341478551764860958), "
                              "[!Quimic](https://discord.com/users/1179587826669592587), "
                              "[Juloxx](https://discord.com/users/1204961543528382467)",
                        inline=False,
                    )
                    team_embed.add_field(
                        name="🤖 Developers",
                        value="[Natrix!](https://discord.com/users/1341478551764860958) (Lead Developer)",
                        inline=False,
                    )
                    team_embed.add_field(
                        name="🎿 Team",
                        value="[Kyra Development™](https://discord.gg/PzekXKbbmm)",
                        inline=False,
                    )
                    await interaction.response.edit_message(embed=team_embed, view=view)
            team_button.callback = team_button_callback
            view.add_item(team_button)

            # Bouton delete
            delete_button = Button(label="🗑️", style=ButtonStyle.red)
            async def delete_button_callback(interaction):
                if interaction.user == ctx.author:
                    await interaction.message.delete()
            delete_button.callback = delete_button_callback
            view.add_item(delete_button)

            # Bouton info serveurs/users
            server_count_button = Button(label=f"Servers: {guild_count} | Users: {user_count}", style=ButtonStyle.success, disabled=True)
            view.add_item(server_count_button)

            await ctx.send(embed=embed, view=view)
            print("✅ Embed envoyé avec succès")

        except Exception as e:
            print("❌ Erreur dans /stats:", e)
            await ctx.send(f"❌ Erreur capturée: `{e}`")

        await processing_message.delete()


async def setup(bot):
    await bot.add_cog(Stats(bot))
