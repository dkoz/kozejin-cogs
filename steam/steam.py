import discord
from redbot.core import commands
import requests
import aiohttp

STEAM_API_KEY = ""

class SteamAPI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def steamprofile(self, ctx, steam_id: str):
        url = f"http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={STEAM_API_KEY}&steamids={steam_id}"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()

        if data and "response" in data and "players" in data["response"] and len(data["response"]["players"]) > 0:
            player = data["response"]["players"][0]
            await ctx.send(f"Player name: {player['personaname']}")
        else:
            await ctx.send("Unable to fetch the player information.")
