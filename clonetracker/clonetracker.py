import discord
from redbot.core import commands
import aiohttp
import json

class CloneTracker(commands.Cog):
    """CloneTracker for Diablo 2: Resurrected"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def clonetracker(self, ctx):
        url = "https://diablo2.io/dclone_api.php?region=1&ladder=1"

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as response:
                    if response.status != 200:
                        await ctx.send("An error occurred while fetching Uber Diablo information.")
                        return

                    data = await response.text()
                    data_json = json.loads(data)
                    
                    if not data_json:
                        await ctx.send("No information available for Uber Diablo in the ladder mode for the Americas region.")
                        return
                    
                    progress = data_json[0]['progress']
                    await ctx.send(f"Uber Diablo is currently {progress}/6 on the ladder in the Americas region.")
            except aiohttp.ClientError as e:
                await ctx.send(f"An error occurred while fetching Uber Diablo information: {str(e)}")