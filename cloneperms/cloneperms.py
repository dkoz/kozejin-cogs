from redbot.core import commands
from discord import TextChannel

class ClonePermissions(commands.Cog):
    """Permission Cloner"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def cloneperms(self, ctx, source: TextChannel, destination: TextChannel):
        """Clones permissions from one channel to another."""
        try:
            permissions = source.overwrites
            await destination.edit(overwrites=permissions)
            await ctx.send(f"Permissions from {source.mention} have been cloned to {destination.mention}.")
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

def setup(bot):
    bot.add_cog(ClonePermissions(bot))
