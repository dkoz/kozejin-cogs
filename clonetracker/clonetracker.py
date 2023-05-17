import discord
from redbot.core import commands
import aiohttp

class CloneTracker(commands.Cog):
    """CloneTracker for Diablo 2: Resurrected"""

    def __init__(self, bot):
        self.bot = bot

    #Not sure if this will work.
    @commands.command()
    async def clonetracker(self, ctx):
        url = "https://diablo2.io/dclone_api.php"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()

        if data["error"]:
            await ctx.send("An error occurred while fetching Uber Diablo information.")
        else:
            await ctx.send(f"Uber Diablo is currently {data['clone_status']} on {data['clone_difficulty']} difficulty.")