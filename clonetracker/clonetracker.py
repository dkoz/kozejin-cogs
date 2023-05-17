import discord
from redbot.core import commands
import aiohttp

class CloneTracker(commands.Cog):
    """CloneTracker for Diablo 2: Resurrected"""

    def __init__(self, bot):
        self.bot = bot

    #Not sure if this will work.
    @commands.command()
    async def diablo(self, ctx):
        url = "https://diablo2.io/dclone_api.php"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as response:
                    if response.content_type != "application/json":
                        await ctx.send("An error occurred while fetching Uber Diablo information. Invalid response format.")
                        return

                    data = await response.json()
            except aiohttp.ClientError as e:
                await ctx.send(f"An error occurred while fetching Uber Diablo information: {str(e)}")
                return

        if data["error"]:
            await ctx.send(f"An error occurred while fetching Uber Diablo information: {data['error']}")
        else:
            await ctx.send(f"Uber Diablo is currently {data['clone_status']} on {data['clone_difficulty']} difficulty.")