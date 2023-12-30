from .cloneperms import ClonePermissions

async def setup(bot):
    await bot.add_cog(ClonePermissions(bot))