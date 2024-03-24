import discord
from redbot.core import commands, Config, data_manager
import asyncio
import aiohttp
import json
import os
from datetime import datetime
import dateutil.parser

class EpicGamesNotifier(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=129495864)
        default_guild = {"channel": None}
        self.config.register_guild(**default_guild)
        self.game_check_task = self.bot.loop.create_task(self.game_check_loop())

        self.db_path = data_manager.cog_data_path(self) / "posted_games.json"
        if not os.path.exists(self.db_path):
            with open(self.db_path, "w") as db_file:
                json.dump([], db_file)

    def cog_unload(self):
        self.game_check_task.cancel()

    async def game_check_loop(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            new_games = await self.check_for_new_games()
            if new_games:
                for guild in self.bot.guilds:
                    channel_id = await self.config.guild(guild).channel()
                    if channel_id:
                        channel = self.bot.get_channel(channel_id)
                        if channel:
                            for game in new_games:
                                if not self.already_posted(game["id"]):
                                    embed = self.create_game_embed(game)
                                    await channel.send(embed=embed)
                                    self.mark_as_posted(game["id"])
            await asyncio.sleep(3600)

    async def check_for_new_games(self):
        url = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    current_free_games = []
                    for game in data["data"]["Catalog"]["searchStore"]["elements"]:
                        if self.is_current_offer(game):
                            current_free_games.append(game)
                    return current_free_games
                else:
                    return []

    def is_current_offer(self, game):
        current_time = datetime.utcnow().isoformat() + "Z"
        promotions = game.get("promotions", {})
        return any(
            promo["promotionalOffers"]
            and promo["promotionalOffers"][0]["startDate"]
            <= current_time
            <= promo["promotionalOffers"][0]["endDate"]
            for promo in promotions.get("promotionalOffers", [])
        )

    def already_posted(self, game_id):
        with open(self.db_path, "r") as db_file:
            posted_games = json.load(db_file)
        return game_id in posted_games

    def mark_as_posted(self, game_id):
        with open(self.db_path, "r") as db_file:
            posted_games = json.load(db_file)
        posted_games.append(game_id)
        with open(self.db_path, "w") as db_file:
            json.dump(posted_games, db_file)

    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @commands.group(name="epicset", aliases=["epic"], invoke_without_command=True)
    async def epic_group(self, ctx):
        """Commands for the Epic Games Notifier"""
        await ctx.send_help(ctx.command)

    @epic_group.command()
    async def setchannel(self, ctx, channel: discord.TextChannel):
        """Set the channel for free game announcements."""
        await self.config.guild(ctx.guild).channel.set(channel.id)
        await ctx.send(f"Channel set to {channel.mention}")

    @epic_group.command()
    async def removechannel(self, ctx):
        """Remove the channel for free game announcements."""
        await self.config.guild(ctx.guild).channel.set(None)
        await ctx.send("Channel for free game announcements has been removed.")

    @epic_group.command()
    async def repost(self, ctx):
        """Repost all currently active free game announcements."""
        with open(self.db_path, "r") as db_file:
            posted_games = json.load(db_file)

        if not posted_games:
            await ctx.send("No games have been posted yet.")
            return

        new_games = await self.check_for_new_games()
        active_games = [game for game in new_games if game["id"] in posted_games]

        if not active_games:
            await ctx.send("No current free games to repost.")
            return

        for game in active_games:
            embed = self.create_game_embed(game)
            await ctx.send(embed=embed)

    def create_game_embed(self, game):
        title = game["title"]
        description = game.get("description", "No description available")

        page_slug = next(
            (
                m["pageSlug"]
                for m in game.get("catalogNs", {}).get("mappings", [])
                if m.get("pageType") == "productHome"
            ),
            None,
        )
        url = (
            f"https://www.epicgames.com/store/en-US/p/{page_slug}"
            if page_slug
            else "https://www.epicgames.com/store/en-US/"
        )

        embed = discord.Embed(title=title, url=url, description=description)
        embed.set_thumbnail(url=game["keyImages"][0]["url"])

        promo_offers = game.get("promotions", {}).get("promotionalOffers", [])
        if promo_offers and promo_offers[0]["promotionalOffers"]:
            start_date = dateutil.parser.parse(
                promo_offers[0]["promotionalOffers"][0].get("startDate")
            ).strftime("%B %d, %Y %H:%M UTC")
            end_date = dateutil.parser.parse(
                promo_offers[0]["promotionalOffers"][0].get("endDate")
            ).strftime("%B %d, %Y %H:%M UTC")
            embed.add_field(name="Promotion Start", value=start_date, inline=True)
            embed.add_field(name="Promotion End", value=end_date, inline=True)

        return embed