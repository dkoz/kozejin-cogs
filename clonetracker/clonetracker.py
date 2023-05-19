import asyncio
import discord
from redbot.core import commands
import aiohttp
import json
import datetime
import urllib.parse

class CloneTracker(commands.Cog):
    """Diablo Clone/Uber Diablo Tracker for Diablo 2: Resurrected"""

    __version__ = "1.0.0"

    def __init__(self, bot):
        self.bot = bot

    async def fetch_uberd_data(self, url):
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as response:
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

    @commands.hybrid_command()
    @commands.bot_has_permissions(embed_links=True)
    async def clonetracker(self, ctx, region: str = "all", ladder: str = "all", hardcore: str = "all"):
        """Search for Diablo on all regions"""
        valid_regions = ["americas", "europe", "asia", "all"]
        valid_ladder = ["ladder", "non-ladder", "all"]
        valid_hardcore = ["hardcore", "softcore", "all"]

        if region.lower() not in valid_regions:
            await ctx.send("Invalid region specified. Valid regions are: Americas, Europe, Asia, All.")
            return

        if ladder.lower() not in valid_ladder:
            await ctx.send("Invalid ladder type specified. Valid types are: Ladder, Non-Ladder, All.")
            return

        if hardcore.lower() not in valid_hardcore:
            await ctx.send("Invalid hardcore type specified. Valid types are: Hardcore, Softcore, All.")
            return

        if region.lower() == "all":
            regions = ["americas", "europe", "asia"]
        else:
            regions = [region.lower()]

        if ladder.lower() == "all":
            ladders = ["ladder", "non-ladder"]
        else:
            ladders = [ladder.lower()]

        if hardcore.lower() == "all":
            hardcore_types = ["hardcore", "softcore"]
        else:
            hardcore_types = [hardcore.lower()]

        for region in regions:
            region_code = await self.get_region_code(region)
            region_name = await self.get_region_name(region_code)

            embed = discord.Embed(title=f"Uber Diablo Information - {region_name}", description="Tracking data for Uber Diablo", color=discord.Color.blue())
            embed.set_footer(text="Data provided by Diablo2.io")

            for ladder in ladders:
                ladder_code = await self.get_ladder_code(ladder)
                ladder_type = await self.get_ladder_type(ladder_code)

                for hardcore_type in hardcore_types:
                    hardcore_code = await self.get_hardcore_code(hardcore_type)
                    hardcore_name = await self.get_hardcore_type(hardcore_code)

                    url = await self.get_uberd_url(region_code, ladder_code, hardcore_code)

                    data = await self.fetch_uberd_data(url)

                    if data is None:
                        await ctx.send("An error occurred while fetching Uber Diablo information.")
                        return

                    if not data:
                        embed.add_field(name=f"{ladder_type} - {hardcore_name}", value="No information available.")
                    else:
                        progress = data[0]['progress']
                        timestamp = data[0]['timestamped']
                        dt = datetime.datetime.fromtimestamp(int(timestamp))
                        formatted_time = dt.strftime("%I:%M %p")
                        embed.add_field(name=f"{ladder_type} - {hardcore_name}", value=f"Progress: {progress}/6\nLast Updated: {formatted_time}", inline=False)

            await ctx.send(embed=embed)

    @commands.command()
    async def clonedatadump(self, ctx, region: str = "all", ladder: str = "all", hardcore: str = "all"):
        """Search for Diablo on all regions (Text Format)"""
        valid_regions = ["americas", "europe", "asia", "all"]
        valid_ladder = ["ladder", "non-ladder", "all"]
        valid_hardcore = ["hardcore", "softcore", "all"]

        if region.lower() not in valid_regions:
            await ctx.send("Invalid region specified. Valid regions are: Americas, Europe, Asia, All.")
            return

        if ladder.lower() not in valid_ladder:
            await ctx.send("Invalid ladder type specified. Valid types are: Ladder, Non-Ladder, All.")
            return

        if hardcore.lower() not in valid_hardcore:
            await ctx.send("Invalid hardcore type specified. Valid types are: Hardcore, Softcore, All.")
            return

        if region.lower() == "all":
            regions = ["americas", "europe", "asia"]
        else:
            regions = [region.lower()]

        if ladder.lower() == "all":
            ladders = ["ladder", "non-ladder"]
        else:
            ladders = [ladder.lower()]

        if hardcore.lower() == "all":
            hardcore_types = ["hardcore", "softcore"]
        else:
            hardcore_types = [hardcore.lower()]

        result = []

        for region in regions:
            region_code = await self.get_region_code(region)
            region_name = await self.get_region_name(region_code)

            for ladder in ladders:
                ladder_code = await self.get_ladder_code(ladder)
                ladder_type = await self.get_ladder_type(ladder_code)

                for hardcore_type in hardcore_types:
                    hardcore_code = await self.get_hardcore_code(hardcore_type)
                    hardcore_name = await self.get_hardcore_type(hardcore_code)

                    url = await self.get_uberd_url(region_code, ladder_code, hardcore_code)

                    data = await self.fetch_uberd_data(url)

                    if data is None:
                        await ctx.send("An error occurred while fetching Uber Diablo information.")
                        return

                    if not data:
                        text = f"No information available for {ladder_type} - {hardcore_name}"
                    else:
                        progress = data[0]['progress']
                        timestamp = data[0]['timestamped']
                        dt = datetime.datetime.fromtimestamp(int(timestamp))
                        formatted_time = dt.strftime("%I:%M %p")
                        text = f"[{progress}/6] - {region_name} - {ladder_type}({hardcore_name}) - [{formatted_time}]"

                    result.append(text)

        if result:
            message = "\n".join(result)
            await ctx.send(message)

    async def get_region_code(self, region):
        if region.lower() == "americas":
            return "1"
        elif region.lower() == "europe":
            return "2"
        elif region.lower() == "asia":
            return "3"
        else:
            return "0"

    async def get_region_name(self, region_code):
        if region_code == "1":
            return "Americas"
        elif region_code == "2":
            return "Europe"
        elif region_code == "3":
            return "Asia"
        else:
            return "Unknown"

    async def get_ladder_code(self, ladder):
        if ladder.lower() == "ladder":
            return "1"
        elif ladder.lower() == "non-ladder":
            return "2"
        else:
            return "0"

    async def get_ladder_type(self, ladder_code):
        if ladder_code == "1":
            return "Ladder"
        elif ladder_code == "2":
            return "Non-Ladder"
        else:
            return "Unknown"

    async def get_hardcore_code(self, hardcore):
        if hardcore.lower() == "hardcore":
            return "1"
        elif hardcore.lower() == "softcore":
            return "2"
        else:
            return "0"

    async def get_hardcore_type(self, hardcore_code):
        if hardcore_code == "1":
            return "Hardcore"
        elif hardcore_code == "2":
            return "Softcore"
        else:
            return "Unknown"