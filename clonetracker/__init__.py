from .clonetracker import CloneTracker

async def setup(bot):
    await bot.add_cog(CloneTracker(bot))