import asyncio
import discord
from redbot.core import commands
import aiohttp
import json
import datetime
from aiocache import cached

class CloneTracker(commands.Cog):
    """Diablo Clone/Uber Diablo Tracker for Diablo 2: Resurrected"""

    __version__ = "1.1.1"

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

    @commands.hybrid_command()
    @commands.bot_has_permissions(embed_links=True)
    async def clonetracker(self, ctx, region: str):
        """
        Search for Uber Diablo in the specified region
        Options: Americas, Europe, Asia or 'all'
        """

        region = region.lower()
        valid_regions = ["americas", "europe", "asia"]
        valid_ladders = ["ladder", "non-ladder"]
        valid_hardcores = ["hardcore", "softcore"]

        if region not in valid_regions and region != "all":
            await ctx.send("Invalid region. Please choose from Americas, Europe, Asia or 'all'.")
            return

        regions_to_search = valid_regions if region == "all" else [region]

        for region in regions_to_search:
            embed = discord.Embed(title=f"Uber Diablo Status - {region.capitalize()}", color=discord.Color.red())
            embed.set_footer(text="Data provided by Diablo2.io")
            for ladder in valid_ladders:
                for hardcore in valid_hardcores:
                    
                    url = await self.get_uberd_url(self.REGIONS[region], self.LADDERS[ladder], self.HARDCORES[hardcore])
                    data = await self.fetch_uberd_data(url)

                    if data is None or not data:
                        error_message = "An error occurred while fetching Uber Diablo information." if data is None else "No information available."
                        embed.add_field(name=f"{ladder.capitalize()} - {hardcore.capitalize()}", value=error_message, inline=False)
                        continue

                    progress = data[0]['progress']
                    timestamp = data[0]['timestamped']
                    dt = datetime.datetime.fromtimestamp(int(timestamp))
                    formatted_time = dt.strftime("%I:%M %p")

                    embed.add_field(name=f"{ladder.capitalize()} - {hardcore.capitalize()}", value=f"Progress: {progress}/6\nLast Updated: {formatted_time}", inline=False)

            await ctx.send(embed=embed)

    @commands.command()
    async def clonetrackersimple(self, ctx, region: str):
        """Dumps Diablo clone data in raw text format"""
        
        region = region.lower()
        valid_regions = ["americas", "europe", "asia"]
        valid_ladders = ["ladder", "non-ladder"]
        valid_hardcores = ["hardcore", "softcore"]

        if region not in valid_regions and region != "all":
            await ctx.send("Invalid region. Please choose from Americas, Europe, Asia or 'all'.")
            return

        regions_to_search = valid_regions if region == "all" else [region]

        messages = []
        for region in regions_to_search:
            for ladder in valid_ladders:
                for hardcore in valid_hardcores:
                    
                    url = await self.get_uberd_url(self.REGIONS[region], self.LADDERS[ladder], self.HARDCORES[hardcore])
                    data = await self.fetch_uberd_data(url)

                    if data is None or not data:
                        error_message = "An error occurred" if data is None else "No information available"
                        messages.append(f"{error_message} for {region.capitalize()} - {ladder.capitalize()} - {hardcore.capitalize()}.")
                        continue

                    progress = data[0]['progress']
                    messages.append(f"[{progress}/6] - {region.capitalize()} - {ladder.capitalize()} - {hardcore.capitalize()}")

        await ctx.send("\n".join(messages))
