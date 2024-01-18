import discord
from redbot.core import commands, Config, data_manager
import asyncio
import aiohttp
import json
import os
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
            with open(self.db_path, 'w') as db_file:
                json.dump({}, db_file)

    def cog_unload(self):
        self.game_check_task.cancel()

    async def game_check_loop(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            for guild in self.bot.guilds:
                channel_id = await self.config.guild(guild).channel()
                if channel_id:
                    channel = self.bot.get_channel(channel_id)
                    if channel:
                        new_games = await self.check_new_games(guild)
                        if new_games:
                            for game in new_games:
                                embed = self.create_game_embed(game)
                                await channel.send(embed=embed)
            await asyncio.sleep(3600)
            
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @commands.group(name="epic", aliases=["ec"], invoke_without_command=True)
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
        """Repost the last game announcement."""
        guild_id = str(ctx.guild.id)
        if os.path.exists(self.db_path):
            with open(self.db_path, 'r') as db_file:
                all_posted_games = json.load(db_file)

            posted_games = all_posted_games.get(guild_id, [])
            if posted_games:
                last_game_id = posted_games[-1]
                url = f"https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions?productId={last_game_id}"
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        if response.status == 200:
                            data = await response.json()
                            game = data['data']['Catalog']['searchStore']['elements'][0]
                            embed = self.create_game_embed(game)
                            await ctx.send(embed=embed)
                        else:
                            await ctx.send("Failed to fetch the game details.")
            else:
                await ctx.send("No previous game announcements found.")
        else:
            await ctx.send("No data file found.")

    def create_game_embed(self, game):
        title = game['title']
        product_slug = game.get('productSlug')

        if product_slug is None and 'catalogNs' in game and 'mappings' in game['catalogNs']:
            for mapping in game['catalogNs']['mappings']:
                if 'pageSlug' in mapping and 'pageType' in mapping and mapping['pageType'] == 'productHome':
                    product_slug = mapping['pageSlug']
                    break

        game_url = f"https://store.epicgames.com/en-US/p/{product_slug}" if product_slug else "URL not available"
        description = game.get('description', 'No description available')

        embed = discord.Embed(title=title, url=game_url, description=description)
        embed.set_thumbnail(url=game['keyImages'][0]['url'])

        promo_offers = game.get('promotions', {}).get('promotionalOffers', [])
        if promo_offers and promo_offers[0]['promotionalOffers']:
            start_date = promo_offers[0]['promotionalOffers'][0].get('startDate')
            end_date = promo_offers[0]['promotionalOffers'][0].get('endDate')

            if start_date and end_date:
                start_date = dateutil.parser.parse(start_date).strftime('%Y-%m-%d %H:%M:%S')
                end_date = dateutil.parser.parse(end_date).strftime('%Y-%m-%d %H:%M:%S')
                embed.add_field(name="Promotion Start", value=start_date, inline=False)
                embed.add_field(name="Promotion End", value=end_date, inline=False)
            else:
                embed.add_field(name="Promotional Offer", value="No promotional dates available", inline=False)
        else:
            embed.add_field(name="Promotional Offer", value="No promotional offers available", inline=False)

        return embed

    async def check_new_games(self, guild):
        url = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    free_games = []

                    if os.path.exists(self.db_path):
                        with open(self.db_path, 'r') as db_file:
                            all_posted_games = json.load(db_file)
                    else:
                        all_posted_games = {}

                    guild_id = str(guild.id)
                    posted_games = all_posted_games.get(guild_id, [])

                    for game in data['data']['Catalog']['searchStore']['elements']:
                        if game['id'] not in posted_games and game.get('promotions') and game['promotions'].get('promotionalOffers'):
                            promotional_offers = game['promotions']['promotionalOffers']
                            if any(promotional_offers):
                                free_games.append(game)
                                posted_games.append(game['id'])

                    all_posted_games[guild_id] = posted_games
                    with open(self.db_path, 'w') as db_file:
                        json.dump(all_posted_games, db_file)

                    return free_games if free_games else None
                else:
                    print(f"Failed to fetch free games: {response.status}")
                    return None
