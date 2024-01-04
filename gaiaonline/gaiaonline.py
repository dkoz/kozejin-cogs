import discord
from redbot.core import commands, Config
import aiohttp
from bs4 import BeautifulSoup
import urllib.parse

class GaiaIntegration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=8475638592, force_registration=True)
        self.config.register_user(gaia_username=None)

    @commands.guild_only()
    @commands.group(name="gaia", aliases=["go"], invoke_without_command=True)
    async def gaia_group(self, ctx):
        """Commands related to Gaia Online."""
        await ctx.send_help(ctx.command)

    @gaia_group.command(name="ava")
    async def gaia_avatar(self, ctx, *, username: str):
        """Search up an avatar on Gaia Online"""
        encoded_username = urllib.parse.quote(username)
        profile_url = f"https://www.gaiaonline.com/profiles/{encoded_username}"

        async with aiohttp.ClientSession() as session:
            async with session.get(profile_url) as response:
                if response.status != 200:
                    await ctx.send(f'Error: Unable to retrieve avatar. HTTP Status: {response.status}')
                    return

                try:
                    soup = BeautifulSoup(await response.text(), 'html.parser')
                except Exception as e:
                    await ctx.send(f'Error parsing HTML: {e}')
                    return

                avatar_img = None
                try:
                    for img in soup.find_all('img', alt=True):
                        alt_text = img['alt'].lower()
                        expected_alt_exact = username.lower()
                        expected_alt_avatar = f"{username.lower()}'s avatar"
                        if alt_text == expected_alt_exact or alt_text == expected_alt_avatar:
                            avatar_img = img['src']
                            break
                except Exception as e:
                    await ctx.send(f'Error searching for avatar image: {e}')
                    return

                if avatar_img:
                    embed = discord.Embed(title=f'{username}\'s Avatar', url=profile_url, color=discord.Color.blue())
                    embed.set_image(url=avatar_img)
                    await ctx.send(embed=embed)
                else:
                    await ctx.send(f'No avatar found for "{username}".')
                    
    @gaia_group.command(name="save")
    async def gaia_save(self, ctx, *, username: str):
        """Save your Gaia Online username."""
        await self.config.user(ctx.author).gaia_username.set(username)
        await ctx.send(f"Gaia Online username saved as: {username}")

    @gaia_group.command(name="me")
    async def gaia_me(self, ctx):
        """Display your saved Gaia Online avatar."""
        username = await self.config.user(ctx.author).gaia_username()
        if not username:
            await ctx.send("You haven't set a username yet. Use `.go save [username]` to save it.")
            return

        await self.gaia_avatar(ctx, username=username)

    @gaia_group.command(name="wipe")
    async def gaia_wipe(self, ctx):
        """Delete your saved Gaia Online username."""
        await self.config.user(ctx.author).clear()
        await ctx.send("Your avatar has been delete from the database.")