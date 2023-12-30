from redbot.core import commands
from discord import TextChannel, Role

class ClonePermissions(commands.Cog):
    """Permission Cloner"""

    def __init__(self, bot):
        self.bot = bot

    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @commands.group(name="clone", aliases=["cl"], invoke_without_command=True)
    async def clone_group(self, ctx):
        """Clone Permissions Commands"""
        await ctx.send_help(ctx.command)

    @clone_group.command()
    async def cloneperms(self, ctx, source: TextChannel, destination: TextChannel):
        """Clones permissions from one channel to another."""
        try:
            permissions = source.overwrites
            await destination.edit(overwrites=permissions)
            await ctx.send(f"Permissions from {source.mention} have been cloned to {destination.mention}.")
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

    @clone_group.command()
    async def resetperms(self, ctx, channel: TextChannel):
        """Resets permissions of a channel to default."""
        try:
            await channel.edit(overwrites={})
            await ctx.send(f"Permissions for {channel.mention} have been reset to default.")
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

    @clone_group.command()
    async def roleperms(self, ctx, role: Role, source: TextChannel, destination: TextChannel):
        """Copies permissions of a specific role from one channel to another."""
        try:
            source_perms = source.overwrites_for(role)
            await destination.set_permissions(role, overwrite=source_perms)
            await ctx.send(f"Permissions for role {role.name} from {source.mention} have been copied to {destination.mention}.")
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

    @clone_group.command()
    async def roletorole(self, ctx, source_role: Role, destination_role: Role):
        """Copies permissions from one role to another."""
        try:
            destination_role_perms = source_role.permissions
            await destination_role.edit(permissions=destination_role_perms)
            await ctx.send(f"Permissions from role {source_role.name} have been copied to role {destination_role.name}.")
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

def setup(bot):
    bot.add_cog(ClonePermissions(bot))
