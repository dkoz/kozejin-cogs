import discord
from redbot.core import commands, Config, app_commands
import asyncio
import aiohttp
from steam.steamid import SteamID
from datetime import datetime
from .steammodal import SteamAPIKeyModal

class SteamAPI(commands.Cog):
    """Search for games and player profiles.

    Grab your [Steam API Key](https://steamcommunity.com/dev/apikey).
    Use the command `[p]setsteamapikey <key here>` to set it.
    
    Then enable the app commands using `[p]slash enablecog steamapp` and `[p]slash sync`.
    You can also enable specific commands; Example: `[p]slash enable steamprofile`."""

    __version__ = "1.0.2"

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=67485765, force_registration=True)
        default_global = {"steam_api_key": None}
        self.config.register_global(**default_global)

    async def resolve_vanity_url(self, ctx, custom_url):
        steam_api_key = await self.config.steam_api_key()
        url = f"http://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/?key={steam_api_key}&vanityurl={custom_url}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise ValueError("Failed to resolve Steam vanity URL.")
                data = await response.json()
                return data.get('response', {}).get('steamid')

    async def get_steamid64(self, ctx, steam):
        if steam.startswith('https://steamcommunity.com/id/') or steam.startswith('http://steamcommunity.com/id/'):
            steam = steam.split('/')[-2]
        elif steam.startswith('https://steamcommunity.com/profiles/') or steam.startswith('http://steamcommunity.com/profiles/'):
            steam = steam.split('/')[-2]

        if steam.isdigit():
            return steam
        elif steam.startswith('STEAM_'):
            steam_id = SteamID(steam)
            return str(steam_id.as_64)
        else:
            return await self.resolve_vanity_url(ctx, steam)

    @commands.command()
    @commands.is_owner()
    async def setsteamapikey(self, ctx, key: str):
        """Set the Steam API key for this bot (Bot Owner Only)."""
        
        if not ctx.channel.permissions_for(ctx.guild.me).manage_messages:
            await ctx.send("I do not have permissions to delete messages in this channel.")
            return

        await self.config.steam_api_key.set(key)
        confirmation_message = await ctx.send("Steam API key has been set for this bot.")
        
        try:
            await ctx.message.delete()
        except discord.NotFound:
            pass
        except discord.Forbidden:
            await ctx.send("I do not have permission to delete messages.", delete_after=5)

        await asyncio.sleep(5)
        
        try:
            await confirmation_message.delete()
        except discord.NotFound:
            pass
        except discord.Forbidden:
            await ctx.send("I do not have permission to delete messages.", delete_after=5)
        
    @app_commands.command(description="Set the Steam API key.")
    @app_commands.guild_only()
    async def steamapikey(self, interaction: discord.Interaction):
        """Open a modal to set the Steam API key (Bot Owner Only)."""
        if interaction.user.id != interaction.client.application.owner.id:
            await interaction.response.send_message("You are not the bot owner.", ephemeral=True)
            return

        try:
            modal = SteamAPIKeyModal(config=self.config)
            await interaction.response.send_modal(modal)
        except Exception as e:
            await interaction.followup.send(str(e), ephemeral=True)

    @app_commands.command(description="Search for user profiles on the Steam database.")
    @app_commands.describe(steam="SteamID64, SteamID, or custom URL.")
    async def steamprofile(self, interaction: discord.Interaction, steam: str):
        """Search for user profiles on the steam database."""
        STEAM_API_KEY = await self.config.steam_api_key()
        if not STEAM_API_KEY:
            await interaction.response.send_message("The Steam API key has not been set. Please set it using the `[p]setsteamapikey` command.", ephemeral=True)
            return

        try:
            steam_id64 = await self.get_steamid64(interaction, steam)
        except ValueError as e:
            await interaction.response.send_message(str(e), ephemeral=True)
            return

        if steam_id64 is None:
            await interaction.response.send_message("Invalid steam profile. Please provide a valid SteamID64, SteamID, or custom URL.", ephemeral=True)
            return

        async with aiohttp.ClientSession() as session:
            async with session.get(f"http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={STEAM_API_KEY}&steamids={steam_id64}") as response:
                if response.status != 200:
                    await interaction.response.send_message("Failed to get player summaries.", ephemeral=True)
                    return
                data = await response.json()

            async with session.get(f"http://api.steampowered.com/ISteamUser/GetPlayerBans/v1/?key={STEAM_API_KEY}&steamids={steam_id64}") as response:
                if response.status != 200:
                    await interaction.response.send_message("Failed to get player bans.", ephemeral=True)
                    return
                ban_data = await response.json()

        if data and "response" in data and "players" in data["response"] and len(data["response"]["players"]) > 0:
            player = data["response"]["players"][0]
            ban_info = ban_data["players"][0] if "players" in ban_data else None
            
            if 'timecreated' in player:
                account_creation_date = datetime.utcfromtimestamp(player['timecreated'])
                account_age = (datetime.utcnow() - account_creation_date).days // 365
            else:
                account_creation_date = None
                account_age = "Unknown"

            steam_id = SteamID(int(steam_id64))
            embed = discord.Embed(
                title=player['personaname'],
                url=f"https://steamcommunity.com/profiles/{steam_id64}",
                color=discord.Color.blue()
            )
            embed.set_thumbnail(url=player['avatarfull'])
            embed.add_field(name="Profile Info", value=f"**Name:** {player.get('realname', 'Unknown')}\n**Country:** {player.get('loccountrycode', 'Unknown')}\n**Account Age:** {account_age} years", inline=True)
            embed.add_field(name="SteamID", value=f"**SteamID:** {steam_id.as_steam2}\n**SteamID3:** [U:1:{steam_id.as_32}]\n**SteamID64:** {steam_id64}", inline=True)
            
            if ban_info is not None:
                ban_info_str = f"**VAC Banned:** {ban_info['VACBanned']}\n"
                ban_info_str += f"**Bans:** {ban_info['NumberOfVACBans']} (Last: {ban_info['DaysSinceLastBan']} days ago)\n"
                ban_info_str += f"**Trade Banned:** {ban_info['EconomyBan']}"
                embed.add_field(name="Ban Info", value=ban_info_str, inline=True)
            
            embed.set_footer(text="Powered by Steam")
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Unable to fetch the player information.", ephemeral=True)
            
    @app_commands.command(description="Search for games on the Steam database.")
    @app_commands.describe(game="Name of the game.")
    async def steamgame(self, interaction: discord.Interaction, game: str):
        """Search for games on the steam database."""
        url = f"https://store.steampowered.com/api/storesearch/?cc=us&l=en&term={game}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()

        if data and data.get('total') > 0:
            best_match = None
            for item in data['items']:
                if item['name'].lower() == game.lower():
                    best_match = item
                    break

            if not best_match:
                best_match = data['items'][0]

            appid = best_match['id']

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
                embed.add_field(name="Price", value=f"{game_info['price_overview']['final_formatted'] if 'price_overview' in game_info else 'Free'}", inline=True)
                embed.add_field(name="Publisher", value=", ".join(game_info['publishers']), inline=True)
                embed.add_field(name="Developer", value=", ".join(game_info['developers']), inline=True)
                embed.add_field(name="Release Date", value=game_info['release_date']['date'], inline=True)
                embed.add_field(name="App ID", value=appid, inline=True)
                embed.add_field(name="Required Age", value=f"{game_info['required_age']}+" if game_info['required_age'] else "None", inline=True)
                embed.add_field(name="Platforms", value=", ".join([platform.capitalize() for platform, available in game_info['platforms'].items() if available]), inline=False)
                embed.set_footer(text="Powered by Steam")

                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message("Unable to fetch the game information.", ephemeral=True)
        else:
            await interaction.response.send_message("Game not found.", ephemeral=True)
