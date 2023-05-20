import asyncio
import discord
from redbot.core import commands
import aiohttp
import json
import datetime
from aiocache import cached

class CloneTracker(commands.Cog):
    """Diablo Clone/Uber Diablo Tracker for Diablo 2: Resurrected"""

    __version__ = "1.0.0"

    # Constants
    REGIONS = {"americas": "1", "europe": "2", "asia": "3", "all": "0"}
    LADDERS = {"ladder": "1", "non-ladder": "2", "all": "0"}
    HARDCORES = {"hardcore": "1", "softcore": "2", "all": "0"}

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    async def cog_cleanup(self):
        await self.session.close()

    @cached(ttl=120)
    async def fetch_uberd_data(self, url):
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    return None
                data = await response.text()
                return json.loads(data)
        except aiohttp.ClientError as e:
            return None

    async def get_uberd_url(self, region_code, ladder_code, hardcore_code):
        base_url = "https://diablo2.io/dclone_api.php"
        url = f"{base_url}?region={region_code}&ladder={ladder_code}&hc={hardcore_code}"
        return url

    async def validate_params(self, ctx, region, ladder, hardcore):
        if region.lower() not in self.REGIONS:
            await ctx.send("Invalid region specified. Valid regions are: Americas, Europe, Asia, All.")
            return False

        if ladder.lower() not in self.LADDERS:
            await ctx.send("Invalid ladder type specified. Valid types are: Ladder, Non-Ladder, All.")
            return False

        if hardcore.lower() not in self.HARDCORES:
            await ctx.send("Invalid hardcore type specified. Valid types are: Hardcore, Softcore, All.")
            return False

        return True

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def clonetracker(self, ctx, region: str = "all", ladder: str = "all", hardcore: str = "all"):
        """Search for Diablo on all regions"""
        if not await self.validate_params(ctx, region, ladder, hardcore):
            return

        region_code = self.REGIONS[region.lower()]
        ladder_code = self.LADDERS[ladder.lower()]
        hardcore_code = self.HARDCORES[hardcore.lower()]

        url = await self.get_uberd_url(region_code, ladder_code, hardcore_code)

        data = await self.fetch_uberd_data(url)

        if data is None:
            await ctx.send("An error occurred while fetching Uber Diablo information.")
            return

        embed = discord.Embed(title="Uber Diablo Status", color=discord.Color.red())

        if not data:
            embed.add_field(name=f"{ladder} - {hardcore}", value="No information available.", inline=False)
        else:
            progress = data[0]['progress']
            timestamp = data[0]['timestamped']
            dt = datetime.datetime.fromtimestamp(int(timestamp))
            formatted_time = dt.strftime("%I:%M %p")
            embed.add_field(name=f"{ladder} - {hardcore}", value=f"Progress: {progress}/6\nLast Updated: {formatted_time}", inline=False)
        
        await ctx.send(embed=embed)

    @commands.command()
    async def clonedatadump(self, ctx, region: str = "all", ladder: str = "all", hardcore: str = "all"):
        """Search for Diablo on all regions (Text Format)"""
        if not await self.validate_params(ctx, region, ladder, hardcore):
            return

        region_code = self.REGIONS[region.lower()]
        ladder_code = self.LADDERS[ladder.lower()]
        hardcore_code = self.HARDCORES[hardcore.lower()]

        url = await self.get_uberd_url(region_code, ladder_code, hardcore_code)

        data = await self.fetch_uberd_data(url)

        if data is None:
            await ctx.send("An error occurred while fetching Uber Diablo information.")
            return

        if not data:
            await ctx.send(f"{ladder} - {hardcore}: No information available.")
        else:
            progress = data[0]['progress']
            timestamp = data[0]['timestamped']
            dt = datetime.datetime.fromtimestamp(int(timestamp))
            formatted_time = dt.strftime("%I:%M %p")
            await ctx.send(f"{ladder} - {hardcore}: Progress: {progress}/6, Last Updated: {formatted_time}")
