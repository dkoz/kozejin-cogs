import discord
from redbot.core import commands
import aiohttp
import json
import datetime

class CloneTracker(commands.Cog):
    """CloneTracker for Diablo 2: Resurrected"""

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command()
    @commands.bot_has_permissions(embed_links=True)
    async def clonetracker(self, ctx, region: str = "all", ladder: str = "all", hardcore: str = "all"):
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
        
        embed = discord.Embed(title="Uber Diablo Information", description="Uber Diablo is a boss in Diablo 2.", color=discord.Color.blue())
        embed.set_footer(text="Data provided by Diablo2.io")
        
        for region in regions:
            region_code = await get_region_code(region)
            region_name = await get_region_name(region_code)
            
            for ladder in ladders:
                ladder_code = await get_ladder_code(ladder)
                ladder_type = await get_ladder_type(ladder_code)
                
                for hardcore_type in hardcore_types:
                    hardcore_code = await get_hardcore_code(hardcore_type)
                    hardcore_name = await get_hardcore_type(hardcore_code)
                    
                    url = f"https://diablo2.io/dclone_api.php?region={region_code}&ladder={ladder_code}&hc={hardcore_code}"
                    
                    async with aiohttp.ClientSession() as session:
                        try:
                            async with session.get(url) as response:
                                if response.status != 200:
                                    await ctx.send("An error occurred while fetching Uber Diablo information.")
                                    return
    
                                data = await response.text()
                                data_json = json.loads(data)
                                
                                if not data_json:
                                    embed.add_field(name=f"{region_name} - {ladder_type} - {hardcore_name}", value="No information available.")
                                else:
                                    progress = data_json[0]['progress']
                                    timestamp = data_json[0]['timestamped']
                                    dt = datetime.datetime.fromtimestamp(int(timestamp))
                                    formatted_time = dt.strftime("%I:%M %p")
                                    embed.add_field(name=f"{region_name} - {ladder_type} - {hardcore_name}", value=f"Progress: {progress}/6\nLast Updated: {formatted_time}", inline=False)
                        except aiohttp.ClientError as e:
                            await ctx.send(f"An error occurred while fetching Uber Diablo information: {str(e)}")
        
        await ctx.send(embed=embed)

async def get_region_code(region):
    if region.lower() == "americas":
        return "1"
    elif region.lower() == "europe":
        return "2"
    elif region.lower() == "asia":
        return "3"
    else:
        return "0"

async def get_region_name(region_code):
    if region_code == "1":
        return "Americas"
    elif region_code == "2":
        return "Europe"
    elif region_code == "3":
        return "Asia"
    else:
        return "Unknown"

async def get_ladder_code(ladder):
    if ladder.lower() == "ladder":
        return "1"
    elif ladder.lower() == "non-ladder":
        return "2"
    else:
        return "0"

async def get_ladder_type(ladder_code):
    if ladder_code == "1":
        return "Ladder"
    elif ladder_code == "2":
        return "Non-Ladder"
    else:
        return "Unknown"

async def get_hardcore_code(hardcore):
    if hardcore.lower() == "hardcore":
        return "1"
    elif hardcore.lower() == "softcore":
        return "2"
    else:
        return "0"

async def get_hardcore_type(hardcore_code):
    if hardcore_code == "1":
        return "Hardcore"
    elif hardcore_code == "2":
        return "Softcore"
    else:
        return "Unknown"