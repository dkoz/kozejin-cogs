from redbot.core import commands, Config, data_manager
import discord
import asyncio
import aiohttp
import json
import os

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
    @commands.command()
    async def setepicchannel(self, ctx, channel: discord.TextChannel):
        """Set the channel for free game announcements."""
        await self.config.guild(ctx.guild).channel.set(channel.id)
        await ctx.send(f"Channel set to {channel.mention}")

    @commands.guild_only()
    @commands.command()
    async def removeepicchannel(self, ctx):
        """Remove the channel for free game announcements."""
        await self.config.guild(ctx.guild).channel.set(None)
        await ctx.send("Channel for free game announcements has been removed.")

    def create_game_embed(self, game):
        title = game['title']
        product_slug = game['productSlug']
        game_url = f"https://epicgames.com/store/product/{product_slug}"
        description = game.get('description', 'No description available')

        embed = discord.Embed(title=title, url=game_url, description=description)
        embed.set_thumbnail(url=game['keyImages'][0]['url'])
        embed.add_field(name="Available Until", value=game['expiryDate'], inline=False)

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
