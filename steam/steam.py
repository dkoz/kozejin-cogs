import discord
from redbot.core import commands, Config
import requests
import aiohttp
from steam.steamid import SteamID

class SteamAPI(commands.Cog):
    """Search for games and player profiles.

    Grab your Steam [API Key](https://steamcommunity.com/dev/apikey).
    Use the command `.setsteamapikey <key here>` to set it."""

    __version__ = "1.0.1"

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=65847657, force_registration=True)
        default_guild = {"steam_api_key": None}
        self.config.register_guild(**default_guild)

    async def resolve_vanity_url(self, ctx, custom_url):
        steam_api_key = await self.config.guild(ctx.guild).steam_api_key()
        url = f"http://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/?key={steam_api_key}&vanityurl={custom_url}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()
        return data['response']['steamid'] if 'response' in data and 'steamid' in data['response'] else None

    async def get_steamid64(self, ctx, identifier):
        if identifier.isdigit():
            return identifier
        elif identifier.startswith('STEAM_'):
            steam_id = SteamID(identifier)
            return str(steam_id.as_64)
        else:
            return await self.resolve_vanity_url(ctx, identifier)
        
    @commands.command()
    @commands.guild_only()
    async def setsteamapikey(self, ctx, key: str):
        """Set the Steam API key for this guild"""
        await self.config.guild(ctx.guild).steam_api_key.set(key)
        await ctx.send("Steam API key has been set for this guild.")

    @commands.command()
    @commands.guild_only()
    async def steamprofile(self, ctx, identifier: str):
        """Search for user profiles on the steam database."""
        STEAM_API_KEY = await self.config.guild(ctx.guild).steam_api_key()
        if not STEAM_API_KEY:
            await ctx.send("The Steam API key has not been set. Please set it using the `setsteamapikey` command.")
            return
            
        steam_id64 = await self.get_steamid64(ctx, identifier)
        if steam_id64 is None:
            await ctx.send("Invalid identifier. Please provide a valid SteamID64, SteamID, or custom URL.")
            return

        async with aiohttp.ClientSession() as session:
            async with session.get(f"http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={STEAM_API_KEY}&steamids={steam_id64}") as response:
                data = await response.json()

            async with session.get(f"http://api.steampowered.com/ISteamUser/GetPlayerBans/v1/?key={STEAM_API_KEY}&steamids={steam_id64}") as response:
                ban_data = await response.json()

        if data and "response" in data and "players" in data["response"] and len(data["response"]["players"]) > 0:
            player = data["response"]["players"][0]

            ban_info = ban_data["players"][0] if "players" in ban_data else None

            steam_id = SteamID(int(steam_id64))

            embed = discord.Embed(
                title=player['personaname'],
                url=f"https://steamcommunity.com/profiles/{steam_id64}",
                color=discord.Color.blue()
            )

            embed.set_thumbnail(url=player['avatarfull'])

            embed.add_field(name="Profile Info", value=f"**Name:** {player.get('realname', 'Unknown')}\n**Country:** {player.get('loccountrycode', 'Unknown')}", inline=True)
            embed.add_field(name="SteamID", value=f"**SteamID:** {steam_id.as_steam2}\n**SteamID3:** [U:1:{steam_id.as_32}]\n**SteamID64:** {steam_id64}", inline=True)

            if ban_info is not None:
                ban_info_str = f"**VAC Banned:** {ban_info['VACBanned']}\n"
                ban_info_str += f"**Bans:** {ban_info['NumberOfVACBans']} (Last: {ban_info['DaysSinceLastBan']} days ago)\n"
                ban_info_str += f"**Trade Banned:** {ban_info['EconomyBan']}"
                embed.add_field(name="Ban Info", value=ban_info_str, inline=True)
                
                embed.set_footer(text="Powered by Steam")

            await ctx.send(embed=embed)
        else:
            await ctx.send("Unable to fetch the player information.")
            
    @commands.command()
    @commands.guild_only()
    async def steamgame(self, ctx, *, name: str):
        """Search for games on the steam database."""
        url = f"https://store.steampowered.com/api/storesearch/?cc=us&l=en&term={name}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()
        
        if data and data.get('total') > 0:
            appid = data['items'][0]['id']
            game_name = data['items'][0]['name']

            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://store.steampowered.com/api/appdetails?appids={appid}&cc=us") as response:
                    data = await response.json()

            if str(appid) in data and data[str(appid)]['success']:
                game_info = data[str(appid)]['data']
                
                embed = discord.Embed(
                    title=game_info['name'],
                    url=f"https://store.steampowered.com/app/{appid}",
                    color=discord.Color.blue()
                )

                embed.set_image(url=game_info['header_image'])

                about_the_game = game_info['short_description']
                if len(about_the_game) > 1024:
                    about_the_game = about_the_game[:1021] + "..."
                embed.add_field(name="About This Game", value=about_the_game, inline=False)

                embed.add_field(name="App ID", value=appid, inline=True)
                embed.add_field(name="Release Date", value=game_info['release_date']['date'], inline=True)
                embed.add_field(name="Price", value=f"{game_info['price_overview']['final_formatted'] if 'price_overview' in game_info else 'Free'}", inline=True)

                embed.add_field(name="Release Date", value=game_info['release_date']['date'], inline=True)
                embed.add_field(name="Publisher", value=", ".join(game_info['publishers']), inline=True)
                embed.add_field(name="Developer", value=", ".join(game_info['developers']), inline=True)

                embed.add_field(name="\u200b", value="\u200b", inline=True)
                embed.add_field(name="\u200b", value="\u200b", inline=True)
                embed.add_field(name="\u200b", value="\u200b", inline=True)
                
                embed.set_footer(text="Powered by Steam")

                await ctx.send(embed=embed)
            else:
                await ctx.send("Unable to fetch the game information.")
        else:
            await ctx.send("Game not found.")