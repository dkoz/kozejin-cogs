import discord
import logging
from redbot.core import commands, app_commands
from mojang import API
from .mcserver import MinecraftServerInfo


class MinecraftAPI(commands.Cog):
    """Cog to look up Minecraft player and server info"""

    def __init__(self, bot):
        self.bot = bot
        self.api = API()
        
    @commands.guild_only()
    @commands.hybrid_group(name="minecraft", aliases=["mc"], invoke_without_command=True)
    async def minecraft(self, ctx: commands.Context):
        """Commands related to Minecraft."""
        await ctx.send_help(ctx.command)

    @minecraft.command(name="player", description="Look up a Minecraft player by name.")
    async def lookupplayer(self, ctx: commands.Context, player: str):
        """Look up a Minecraft player's profile"""
        try:
            await ctx.defer()
            uuid = self.api.get_uuid(player)
            if not uuid:
                await ctx.send(f"Player '{player}' not found.", ephemeral=True)
                return

            head_url = f"https://crafthead.net/avatar/{uuid}"
            body_url = f"https://crafthead.net/body/{uuid}"

            embed = discord.Embed(
                title=f"Player: {player}",
                description=f"You have looked up {player}!",
                url=f"https://namemc.com/profile/{uuid}",
                color=discord.Color.blurple()
            )
            embed.set_thumbnail(url=head_url)
            embed.set_image(url=body_url)
            embed.add_field(name="UUID", value=f"```{uuid}```", inline=True)

            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"An error occurred: {e}", ephemeral=True)
            logging.error(f"An error occurred: {e}")

    @minecraft.command(name="cape", description="Look up a Minecraft player's cape by name.")
    async def lookupcape(self, ctx: commands.Context, player: str):
        """Look up a Minecraft player's cape"""
        try:
            await ctx.defer()
            uuid = self.api.get_uuid(player)
            if not uuid:
                await ctx.send(f"Player '{player}' not found.", ephemeral=True)
                return

            cape_url = f"https://crafthead.net/cape/{uuid}"

            embed = discord.Embed(
                title=f"Player: {player}",
                description=f"You have looked up {player}'s cape!",
                url=f"https://namemc.com/profile/{uuid}",
                color=discord.Color.blurple()
            )
            embed.set_image(url=cape_url)

            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"{player} does not exist.", ephemeral=True)
            logging.error(f"An error occurred: {e}")

    @minecraft.command(name="skin", description="Look up a Minecraft player's skin by name.")
    async def lookupskin(self, ctx: commands.Context, player: str):
        """Look up a Minecraft player's skin"""
        try:
            await ctx.defer()
            uuid = self.api.get_uuid(player)
            if not uuid:
                await ctx.send(f"Player '{player}' not found.", ephemeral=True)
                return

            skin_url = f"https://crafthead.net/skin/{uuid}"

            embed = discord.Embed(
                title=f"Player: {player}",
                description=f"You have looked up {player}'s skin!",
                url=f"https://namemc.com/profile/{uuid}",
                color=discord.Color.blurple()
            )
            embed.set_image(url=skin_url)

            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"{player} does not exist.", ephemeral=True)
            logging.error(f"An error occurred: {e}")
            
    @minecraft.command(name="server", description="Get full information about a Minecraft server.")
    async def serverinfo(self, ctx: commands.Context, server_ip: str):
        """Look up Minecraft server info"""
        try:
            await MinecraftServerInfo.server_info(ctx, server_ip)
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")