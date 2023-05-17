import discord
from redbot.core import commands
import aiohttp
import json

class CloneTracker(commands.Cog):
    """CloneTracker for Diablo 2: Resurrected"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def clonetracker(self, ctx, region: str):
        valid_regions = ["americas", "europe", "asia"]
        
        if region.lower() not in valid_regions:
            await ctx.send("Invalid region specified. Valid regions are: Americas, Europe, Asia.")
            return
        
        region_code = await get_region_code(region.lower())
        
        url = f"https://diablo2.io/dclone_api.php?region={region_code}&ladder=1"

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as response:
                    if response.status != 200:
                        await ctx.send("An error occurred while fetching Uber Diablo information.")
                        return

                    data = await response.text()
                    data_json = json.loads(data)
                    
                    if not data_json:
                        await ctx.send(f"No information available for Uber Diablo in the ladder mode for the {region.capitalize()} region.")
                        return
                    
                    progress = data_json[0]['progress']
                    ladder = data_json[0]['ladder']
                    region_name = await get_region_name(region_code)
                    ladder_type = await get_ladder_type(ladder)
                    
                    embed = discord.Embed(title="Uber Diablo Information", description="Uber Diablo is a boss in Diablo 2.", color=discord.Color.blue())
                    embed.add_field(name="Progress", value=f"{progress}/6")
                    embed.add_field(name="Ladder", value=ladder_type)
                    embed.add_field(name="Region", value=region_name)
                    embed.set_footer(text="Data provided by Diablo2.io")
                    
                    await ctx.send(embed=embed)
            except aiohttp.ClientError as e:
                await ctx.send(f"An error occurred while fetching Uber Diablo information: {str(e)}")

async def get_region_code(region):
    if region == "americas":
        return "1"
    elif region == "europe":
        return "2"
    elif region == "asia":
        return "3"
    else:
        return "0"

async def get_region_name(region):
    if region == "1":
        return "Americas"
    elif region == "2":
        return "Europe"
    elif region == "3":
        return "Asia"
    else:
        return "Unknown"

async def get_ladder_type(ladder):
    if ladder == "1":
        return "Ladder"
    elif ladder == "2":
        return "Non-Ladder"
    else:
        return "Unknown"